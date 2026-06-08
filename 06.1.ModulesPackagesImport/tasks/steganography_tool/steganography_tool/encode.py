import numpy as np


def encode_message(data: np.ndarray, message: str) -> np.ndarray:
    encoded = data.copy()
    payload = message.encode("utf-8") + b"\x00"
    bits = "".join(f"{byte:08b}" for byte in payload)

    flat = encoded.reshape(-1)
    if len(bits) > len(flat):
        raise ValueError("Message is too large for this image")

    for i, bit in enumerate(bits):
        flat[i] = (int(flat[i]) & ~1) | int(bit)
    return encoded
