from datetime import datetime
from pathlib import Path

directory = Path('/Users/just_bsi/PycharmProjects/test_work/src/storage')


def get_all_files(path):
    result = []
    for path in directory.glob('**'):
        for file in path.glob('*'):
            if file.is_file():
                path = file
                name = file.stem
                exception = file.suffix
                size = file.stat().st_size
                created_at = datetime.fromtimestamp(file.stat().st_birthtime)
                updated_at = datetime.fromtimestamp(file.stat().st_mtime)
                result.append([str(path), name, exception, size, created_at, updated_at])
    return result



get_all_files(directory)
