from shutil import copyfileobj
from datetime import datetime
from pathlib import Path


from fastapi import HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select, insert, delete, update

from src.files import strings
from src.files.models import File
from src.files.schemas import FileModel
from src.config import STORAGE_PATH as STORAGE

storage = Path(STORAGE)


def _file_path_to_attr(file_path: str) -> (str, str, str):
    file_path = Path(file_path)

    name = file_path.stem
    extension = file_path.suffix
    path = '/' if str(file_path.parent) == '/' else str(file_path.parent)+'/'

    return name, extension, path


async def get_all_files_infos(session) -> list[FileModel]:
    query = select(File)
    result = await session.execute(query)
    result = result.scalars().all()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strings.NO_FILE_FOUND)

    return result


async def get_file_info(file_path: str, session) -> FileModel:
    name, extension, path = _file_path_to_attr(file_path)

    query = (select(File)
             .where(File.name == name)
             .where(File.extension == extension)
             .where(File.path == path))

    result = await session.execute(query)
    result = result.scalars().first()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strings.NO_FILE_CHECK_PATH)

    return result


async def upload_file(session, file: UploadFile, path: str = '/', comment: str | None = None,
                      exist_ok: bool = False) -> None:
    full_path = storage / path[1:]
    full_path.mkdir(parents=True, exist_ok=True)
    file_full_path = full_path / file.filename
    updated_at = None if not file_full_path.exists() else datetime.now()

    if file_full_path.exists() and not exist_ok:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=strings.FILE_ALREADY_EXIST)

    with open(file_full_path, 'wb') as f:
        copyfileobj(file.file, f)

    file.file.close()

    file_data = {
        'name': file_full_path.stem,
        'extension': file_full_path.suffix,
        'size': file_full_path.stat().st_size,
        'path': path,
        'updated_at': updated_at,
        'comment': comment
    }

    if updated_at:
        stmt = (update(File).values(updated_at=updated_at)
                .where(File.name == file_data['name'])
                .where(File.extension == file_data['extension'])
                .where(File.path == file_data['path']))
    else:
        stmt = insert(File).values(**file_data)

    await session.execute(stmt)
    await session.commit()


async def delete_file(file_path: str, session) -> None:
    full_file_path = storage / file_path[1:]
    if not full_file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strings.NO_FILE_CHECK_PATH)

    name, extension, path = _file_path_to_attr(file_path)
    stmt = (delete(File)
            .where(File.name == name)
            .where(File.extension == extension)
            .where(File.path == path))

    full_file_path.unlink()

    await session.execute(stmt)
    await session.commit()


async def get_files_infos_by_path(session, path: str = '/') -> list[FileModel]:
    query = select(File).where(File.path == path)
    result = await session.execute(query)
    result = result.scalars().all()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strings.NO_FILE_CHECK_PATH)

    return result


async def download_file(file_path: str) -> FileResponse:
    full_path = storage / file_path[1:]
    if not full_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strings.NO_FILE_CHECK_PATH)

    return FileResponse(full_path)


async def update_file_info(session, file_path: str, new_name: str | None = None, new_path: str | None = None,
                           new_comment: str | None = None) -> None:
    full_file_path = storage / file_path[1:]
    if not full_file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strings.NO_FILE_CHECK_PATH)

    file_info = await get_file_info(file_path, session)
    updated_at = datetime.now() if new_name or new_path or new_comment else file_info.updated_at
    new_name = new_name or file_info.name
    new_path = new_path or file_info.path
    new_comment = new_comment or file_info.comment

    new_full_path = storage / new_path[1:]

    new_full_path.mkdir(parents=True, exist_ok=True)

    full_file_path.replace(new_full_path / (new_name + file_info.extension))

    stmt = (update(File).values(name=new_name, path=new_path, comment=new_comment, updated_at=updated_at)
            .where(File.name == file_info.name)
            .where(File.extension == file_info.extension)
            .where(File.path == file_info.path))

    await session.execute(stmt)
    await session.commit()


async def sync_db_with_storage(session) -> None:
    files_in_db = await session.execute(select(File))
    files_in_db = files_in_db.scalars().all()
    files_in_db = {Path(file.path) / (file.name + file.extension) for file in files_in_db}
    files_in_storage = set(storage.rglob('*.*'))

    for file in files_in_db:
        if storage / str(file)[1:] not in files_in_storage:
            name, extension, path = _file_path_to_attr(file)

            stmt = (delete(File)
                    .where(File.name == name)
                    .where(File.extension == extension)
                    .where(File.path == path))
            await session.execute(stmt)

    files_in_db = {storage / str(file)[1:] for file in files_in_db}
    for file in files_in_storage:
        if file not in files_in_db:
            file_data = {
                'name': file.stem,
                'extension': file.suffix,
                'size': file.stat().st_size,
                'path': '/' if file.parent == storage else '/'+'/'.join(file.parts[len(storage.parts):-1])+'/'
            }
            stmt = insert(File).values(name=file_data['name'] ,extension=file_data['extension'] ,size=file_data['size'],
                                       path=file_data['path'])
            await session.execute(stmt)

    await session.commit()
