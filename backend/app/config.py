from pydantic import BaseModel

class Settings(BaseModel):
    model_id: str = "Qwen/Qwen2-VL-2B-Instruct"
    quant_4bit: bool = True
    use_cpu: bool = False
    device_map: str = "auto"
    max_image_edge: int = 1024
    max_new_tokens: int = 512

settings = Settings()
