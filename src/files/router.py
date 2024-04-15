import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from anyio.streams import file
from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.files.models import File
from fastapi_cache.decorator import cache

from src.files.schemas import FileCreate

router = APIRouter(
    prefix="",
    tags=["file"]
)

storage = '/Users/just_bsi/PycharmProjects/test_work/src/storage'


@router.get("/files", response_model=List[FileCreate])
async def get_all_files_infos(session: AsyncSession = Depends(get_async_session)):
    query = select(File.name, File.extension, File.size, File.path, File.created_at, File.updated_at, File.comment)
    result = await session.execute(query)
    return result.mappings().all()


@router.get("/file", response_model=FileCreate)
async def get_file_info(full_path: str, session: AsyncSession = Depends(get_async_session)):
    full_path = Path(full_path)
    name = full_path.stem
    extension = full_path.suffix
    path = str(Path(storage).joinpath(full_path.parent))

    query = (select(File.name, File.extension, File.size, File.path, File.created_at, File.updated_at, File.comment).
             where(File.name == name).where(File.extension == extension).where(File.path == path))
    result = await session.execute(query)
    return result.mappings().first()  #TODO разобраться с форматом и валидацией


@router.post("/upload", description='Empty "path" means root path.')
async def upload_new_file(new_file: UploadFile, path: str | None = None, comment: str | None = None,
                          exist_ok: bool = False, session: AsyncSession = Depends(get_async_session)):
    root_path = Path(storage).joinpath(path) if path else Path(storage)
    root_path.mkdir(parents=True, exist_ok=True)
    full_path = root_path.joinpath(new_file.filename)

    if (full_path.exists() and exist_ok) or not full_path.exists():
        updated_at = None if not full_path.exists() else datetime.now()
        with open(full_path, 'wb') as f:
            shutil.copyfileobj(new_file.file, f)
    else:
        return {'error': 'File already exists'}

    file_infos = root_path

    file_data = {
        'name': full_path.stem,
        'extension': full_path.suffix,
        'size': full_path.stat().st_size,
        'path': str(file_infos),
        'created_at': datetime.now(),
        'updated_at': updated_at,
        'comment': comment
    }

    new_file.file.close()

    if updated_at:
        stmt = (update(File).values(updated_at=updated_at).where(File.name == full_path.stem).
                where(File.extension == full_path.suffix).where(File.path == str(file_infos)))
    else:
        stmt = insert(File).values(**file_data)
    await session.execute(stmt)
    await session.commit()

    if updated_at:
        return {'file updated': file_data}
    else:
        return {'new file uploaded': file_data}


@router.delete("/delete")
async def delete_file(full_path: str, session: AsyncSession = Depends(get_async_session)):
    full_path = Path(full_path)
    name = full_path.stem
    extension = full_path.suffix
    path = str(Path(storage).joinpath(full_path.parent))

    Path(storage).joinpath(full_path).unlink()
    query = delete(File).where(File.name == name).where(File.extension == extension).where(File.path == path)
    await session.execute(query)
    await session.commit()
    return {'file deleted': full_path}


@router.get("/path", response_model=FileCreate | List[FileCreate])
async def get_files_infos_by_dir(path: str | None = None, session: AsyncSession = Depends(get_async_session)):
    full_path = str(Path(storage).joinpath(Path(path))) if path else str(Path(storage))
    query = select(File.name, File.extension, File.size, File.path, File.created_at, File.updated_at,
                   File.comment).where(File.path == full_path)
    result = await session.execute(query)
    return result.mappings().all()


@router.get("/download")
async def download_file_by_id(full_path: str):
    file_path = Path(storage).joinpath(full_path)
    if not file_path.exists():
        return {'error': 'File does not exist'}

    return FileResponse(file_path)


@router.patch("/update")
async def update_file_info(full_path: str, new_name: str | None = None, new_path: str | None = None,
                           new_comment: str | None = None, session: AsyncSession = Depends(get_async_session)):

    file_path = Path(storage).joinpath(full_path)
    if not file_path.exists():
        return {'error': 'File does not exist'}

    file_info = await get_file_info(full_path, session)

    new_name = file_info.name if not new_name else new_name
    new_path = file_info.path if not new_path else str(Path(storage).joinpath(new_path))
    new_comment = file_info.comment if not new_comment else new_comment

    Path(new_path).mkdir(parents=True, exist_ok=True)

    file_path.replace(Path(storage).joinpath(new_path, new_name + file_info.extension))

    stmt = (update(File).values(name=new_name, path=new_path, comment=new_comment, updated_at=datetime.now()).
            where(File.name == file_info.name).where(File.extension == file_info.extension).
            where(File.path == file_info.path))
    await session.execute(stmt)
    await session.commit()
    return {'file updated'}


@router.get("/sync")
async def sync_db_with_files(session: AsyncSession = Depends(get_async_session)):
    files_in_db = await get_all_files_infos(session)
    filesss = [str(Path(files_in_db.path).joinpath(files_in_db.name + files_in_db.extension)) for files_in_db in files_in_db]
    all_files = Path(storage).rglob('*.*')
    # print(all_files)
    # print(filesss)
    # print(files_in_db)

    for file in all_files:
        if str(file) not in filesss:
            file_data = {
                'name': file.stem,
                'extension': file.suffix,
                'size': file.stat().st_size,
                'path': str(file.parent),
                'created_at': datetime.now()
            }
            stmt = insert(File).values(**file_data)
            await session.execute(stmt)

    for file in filesss:
        if file not in all_files:
            file = Path(file)
            name = file.stem
            extension = file.suffix
            path = str(Path(storage).joinpath(file.parent))

            query = delete(File).where(File.name == name).where(File.extension == extension).where(File.path == path)
            await session.execute(query)

    await session.commit()
