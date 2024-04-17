from pathlib import Path
from typing import Any


def full_path_to_attr(full_path: str) -> Any:
    full_path = Path(full_path)
    name = full_path.stem
    extension = full_path.suffix
    path = str(full_path.parent)

    return name, extension, path
