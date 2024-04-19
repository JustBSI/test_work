from pathlib import Path


def full_path_to_attr(full_path: str) -> (str, str, str):
    full_path = Path(full_path)
    name = full_path.stem
    extension = full_path.suffix
    path = str(full_path.parent)

    return name, extension, path
