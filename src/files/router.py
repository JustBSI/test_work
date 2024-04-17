import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Any

from anyio.streams import file
from fastapi import APIRouter, Depends, UploadFile, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.files.models import File
from src.files.services import full_path_to_attr
from fastapi_cache.decorator import cache

from src.files.schemas import FileCreate

router = APIRouter(
    prefix="",
    tags=["file"]
)

storage = Path('/Users/just_bsi/PycharmProjects/test_work/src/storage')


@router.get("/files", response_model=List[FileCreate], status_code=status.HTTP_200_OK)
async def get_all_files_infos(session: AsyncSession = Depends(get_async_session)):
    """
    Get all file infos.
    """

    query = select(File)
    result = await session.execute(query)
    result = result.scalars().all()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No files found.")
    return result


@router.get("/file", response_model=FileCreate, status_code=status.HTTP_200_OK)
async def get_file_info_by_full_path(full_path: str, session: AsyncSession = Depends(get_async_session)):
    """
    Get file info by full path.\n
    Full path example: storage/pics/Photo.jpg\n
    Empty full path means root path.
    """

    name, extension, path = full_path_to_attr(full_path)

    query = select(File).where(File.name == name).where(File.extension == extension).where(File.path == path)
    result = await session.execute(query)
    result = result.scalars().first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found, check path.")
    return result


@router.post("/upload", description='Empty "path" means root path. If "exist_ok"=True, '
                                    'file will be overwritten if exists, else raise error.',
             status_code=status.HTTP_201_CREATED)
async def upload_file(new_file: UploadFile, path: str | None = None, comment: str | None = None,
                      exist_ok: bool = False, session: AsyncSession = Depends(get_async_session)):
    root_path = storage.joinpath(path) if path else storage
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


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_by_full_path(full_path: str, session: AsyncSession = Depends(get_async_session)):
    """
    Delete file from storage and db by full path.\n
    Full path example: storage/pics/Photo.jpg\n
    Empty full path means root path.
    """
    if not Path(full_path).is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found, check path.")

    name, extension, path = full_path_to_attr(full_path)
    query = delete(File).where(File.name == name).where(File.extension == extension).where(File.path == path)
    await session.execute(query)
    await session.commit()


@router.get("/path", response_model=List[FileCreate], status_code=status.HTTP_200_OK)
async def get_files_infos_by_path(path: str, session: AsyncSession = Depends(get_async_session)):
    """
    Get files infos by path.\n
    Path example: storage/pics\n
    Empty full path means root path.
    """
    query = select(File).where(File.path == str(Path(path)))
    result = await session.execute(query)
    result = result.scalars().all()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No files found, check path.")
    return result


@router.get("/download", status_code=status.HTTP_200_OK, response_class=FileResponse)
async def download_file_by_(full_path: str):
    """
    Download file by full path.\n
    Path example: storage/pics/Photo.jpg\n
    Empty full path means root path.
    """
    if not Path(full_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found, check path.")

    return FileResponse(full_path)


@router.patch("/update", status_code=status.HTTP_200_OK)
async def update_file_info(full_path: str, new_name: str | None = None, new_path: str | None = None,
                           new_comment: str | None = None, session: AsyncSession = Depends(get_async_session)):
    """
    Update file info by full path.\n
    Path example: storage/pics/Photo.jpg\n
    Empty full path means root path.
    """
    file_path = Path(full_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found, check path.")

    file_info = await get_file_info_by_full_path(full_path, session)

    new_name = new_name or file_info.name
    new_path = new_path or file_info.path
    new_comment = new_comment or file_info.comment

    Path(new_path).mkdir(parents=True, exist_ok=True)

    file_path.replace(new_path.joinpath(new_name + file_info.extension))

    stmt = (update(File).values(name=new_name, path=new_path, comment=new_comment, updated_at=datetime.now()).
            where(File.name == file_info.name).where(File.extension == file_info.extension).
            where(File.path == file_info.path))
    await session.execute(stmt)
    await session.commit()


@router.get("/sync", status_code=status.HTTP_200_OK)
async def sync_db_with_files(session: AsyncSession = Depends(get_async_session)):
    """
    Sync db info with storage.
    """
    files_in_db = await get_all_files_infos(session)
    files_in_db = [str(Path(files_in_db.path).joinpath(files_in_db.name + files_in_db.extension)) for files_in_db in
                   files_in_db]
    files_in_storage = storage.rglob('*.*')

    for file in files_in_storage:
        if str(file) not in files_in_db:
            file_data = {
                'name': file.stem,
                'extension': file.suffix,
                'size': file.stat().st_size,
                'path': str(file.parent),
                'created_at': datetime.now()
            }
            stmt = insert(File).values(**file_data)
            await session.execute(stmt)

    for file in files_in_db:
        if file not in files_in_storage:
            file = Path(file)
            name = file.stem
            extension = file.suffix
            path = str(storage.joinpath(file.parent))

            query = delete(File).where(File.name == name).where(File.extension == extension).where(File.path == path)
            await session.execute(query)

    await session.commit()
