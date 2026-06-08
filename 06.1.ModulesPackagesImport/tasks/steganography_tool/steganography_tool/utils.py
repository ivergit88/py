from pathlib import Path

import numpy as np
from PIL import Image


def _data_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "lenna.png"


def read_file(filename: str | Path) -> np.ndarray:
    return np.array(Image.open(filename))


def write_file(data: np.ndarray, filename: str | Path) -> None:
    Image.fromarray(data.astype(np.uint8)).save(filename)


def get_base_file() -> np.ndarray:
    return read_file(_data_path())
