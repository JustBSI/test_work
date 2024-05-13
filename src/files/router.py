from typing import List

from fastapi import APIRouter, UploadFile, status
from fastapi.responses import FileResponse

from src.files.schemas import FileModel
from src.files.services import FileService as File, StorageService as Storage

router = APIRouter(
    prefix="/files",
    tags=["file"]
)


@router.get("/", response_model=List[FileModel], status_code=status.HTTP_200_OK, response_description='List of files')
async def get_all_files_infos():
    return await Storage().get_all_files_infos()


@router.get("/file", response_model=FileModel, status_code=status.HTTP_200_OK, response_description='File')
async def get_file_info(file_path: str):
    """
    File path example: /pics/cats/Photo.jpg or /Photo.jpg\n
    '/' path means storage path.
    """
    return await File().get_file_info(file_path)


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_description='File uploaded')
async def upload_file(file: UploadFile, path: str = '/', comment: str | None = None, exist_ok: bool = False):
    """
    Path example: /pics/cats/ or /\n
    '/' path means storage path.\n
    If "exist_ok"=True, file will be overwritten if exists, else raise error.
    """
    await File().upload_file(file, path, comment, exist_ok)


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT, response_description='File deleted')
async def delete_file(file_path: str):
    """
    File path example: /pics/cats/Photo.jpg or /Photo.jpg\n
    '/' path means storage path.
    """
    await File().delete_file(file_path)


@router.get("/path", response_model=List[FileModel], status_code=status.HTTP_200_OK,
            response_description='List of files in path')
async def get_files_infos_by_path(path: str = '/'):
    """
    Path example: /pics/cats/\n
    '/' path means storage path.
    """
    return await Storage().get_files_infos_by_path(path)


@router.get("/download", status_code=status.HTTP_200_OK, response_class=FileResponse, response_description='File')
async def download_file(file_path: str):
    """
    File path example: /pics/cats/Photo.jpg or /Photo.jpg\n
    '/' path means storage path.
    """
    return await File().download_file(file_path)


@router.patch("/update", status_code=status.HTTP_200_OK, response_description='File updated')
async def update_file_info(file_path: str, new_name: str | None = None, new_path: str | None = None,
                           new_comment: str | None = None):
    """
    File path example: /pics/cats/Photo.jpg or /Photo.jpg\n
    '/' path or new_path means storage path.\n
    If new_path is None, file will be updated without change path.
    """
    await File().update_file_info(file_path, new_name, new_path, new_comment)


@router.get("/sync", status_code=status.HTTP_200_OK, response_description='Storage == db')
async def sync_db_with_storage():
    await Storage().sync_db_with_storage()
