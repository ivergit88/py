import numpy as np


def decode_message(data: np.ndarray) -> str:
    bits = "".join(str(int(value) & 1) for value in data.reshape(-1))
    result = bytearray()

    for i in range(0, len(bits), 8):
        chunk = bits[i:i + 8]
        if len(chunk) < 8:
            break
        value = int(chunk, 2)
        if value == 0:
            break
        result.append(value)

    return result.decode("utf-8", errors="ignore")
