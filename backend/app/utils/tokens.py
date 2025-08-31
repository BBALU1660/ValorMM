def rough_token_estimate(text: str) -> int:
    return max(1, len(text) // 4)
