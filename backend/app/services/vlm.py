import time, threading
from typing import List, Tuple, Dict, Any, Iterable
import torch
from transformers import AutoProcessor, BitsAndBytesConfig, TextIteratorStreamer
try:
    from transformers import Qwen2VLForConditionalGeneration
except Exception as e:
    raise RuntimeError("Transformers missing Qwen2VL classes. Update transformers >= 4.43.") from e

from .images import resize_long_edge

_MODEL_CACHE: Dict[Tuple[str,bool,bool,int], Tuple[Qwen2VLForConditionalGeneration, AutoProcessor]] = {}

def get_model(model_id: str, quant_4bit: bool, use_cpu: bool, max_image_edge: int):
    key = (model_id, quant_4bit, use_cpu, max_image_edge)
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    qconf = None
    if quant_4bit:
        qconf = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16)

    dtype = torch.float32 if use_cpu else torch.float16
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id,
        trust_remote_code=True,
        device_map="auto",
        torch_dtype=dtype,
        quantization_config=qconf
    )
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    _MODEL_CACHE[key] = (model, processor)
    return _MODEL_CACHE[key]

def build_msgs(history: List[Dict[str,str]], user_text: str, images: List) -> List[Dict[str, Any]]:
    msgs: List[Dict[str, Any]] = []
    for h in history:
        role = "user" if h.get("role") == "user" else "assistant"
        msgs.append({"role": role, "content": [{"type":"text","text": h.get("content","")}]})
    content = [ {"type":"image","image":im} for im in images ]
    content.append({"type":"text","text": user_text})
    msgs.append({"role":"user","content":content})
    return msgs

def chat_once(model_id: str, quant_4bit: bool, use_cpu: bool, max_image_edge: int, max_new_tokens: int,
              history: List[Dict[str,str]], user_text: str, images: List):
    from qwen_vl_utils import process_vision_info
    model, processor = get_model(model_id, quant_4bit, use_cpu, max_image_edge)
    images = [resize_long_edge(im, max_image_edge) for im in images]
    msgs = build_msgs(history, user_text, images)

    prompt = processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    vi, vv = process_vision_info(msgs)
    inputs = processor(text=[prompt], images=vi, videos=vv, return_tensors="pt")
    if model.device.type == "cuda":
        inputs = {k: v.to(model.device, non_blocking=True) for k, v in inputs.items()}

    t0 = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False, temperature=0.0,
            top_p=1.0, return_dict_in_generate=True
        )
    latency_ms = int((time.time() - t0) * 1000)

    prompt_len = int(inputs["input_ids"].shape[1])
    generated = outputs.sequences[:, prompt_len:]
    text = processor.batch_decode(generated, skip_special_tokens=True)[0].strip()

    prompt_tokens = prompt_len
    completion_tokens = int(generated.shape[1])
    usage = {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "latency_ms": latency_ms}
    return text, usage

def stream_chat_once(model_id: str, quant_4bit: bool, use_cpu: bool, max_image_edge: int, max_new_tokens: int,
                     history: List[Dict[str,str]], user_text: str, images: List) -> Iterable[str]:
    """Streaming generator yielding only assistant text (no role preamble), spaces preserved."""
    from qwen_vl_utils import process_vision_info

    model, processor = get_model(model_id, quant_4bit, use_cpu, max_image_edge)
    images = [resize_long_edge(im, max_image_edge) for im in images]
    msgs = build_msgs(history, user_text, images)

    prompt = processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    vi, vv = process_vision_info(msgs)
    inputs = processor(text=[prompt], images=vi, videos=vv, return_tensors="pt")
    if model.device.type == "cuda":
        inputs = {k: v.to(model.device, non_blocking=True) for k, v in inputs.items()}

    tokenizer = getattr(processor, "tokenizer", None)
    if tokenizer is None:
        raise RuntimeError("Processor has no tokenizer; update transformers/qwen-vl-utils.")

    streamer = TextIteratorStreamer(tokenizer, skip_special_tokens=True, decode_kwargs={"skip_special_tokens": True})
    gen_kwargs = dict(
        **inputs, max_new_tokens=max_new_tokens, do_sample=False, temperature=0.0, top_p=1.0, streamer=streamer
    )

    thread = threading.Thread(target=model.generate, kwargs=gen_kwargs)
    thread.start()

    prebuf = ""
    cleaned = False
    marker = "assistant\n"  # Qwen chat template marker

    for chunk in streamer:
        if not chunk:
            continue
        if not cleaned:
            prebuf += chunk
            # strip everything up to and including last 'assistant\n'
            idx = prebuf.rfind(marker)
            if idx != -1:
                cleaned = True
                rest = prebuf[idx + len(marker):]
                if rest:
                    yield rest
                prebuf = ""
            # else keep buffering until marker appears
        else:
            # pass through untouched (do not trim)
            yield chunk
