from shutil import copyfileobj
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select, insert, delete, update

from src.files.strings import ExceptionStrings
from src.files.models import File
from src.files.schemas import FileModel
from src.config import Config
from src.database import DbRequest


class BaseService:

    def __init__(self):
        self.storage = Path(Config.STORAGE_PATH)
        self.db = DbRequest()

    @classmethod
    def __file_path_to_attr(cls, file_path: str) -> (str, str, str):
        file_path = Path(file_path)

        name = file_path.stem
        extension = file_path.suffix
        path = '/' if str(file_path.parent) == '/' else str(file_path.parent) + '/'

        return name, extension, path

    def __check_file_exists(self, file_path: str) -> Path | None:
        file_full_path = self.storage / file_path[1:]
        if not file_full_path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ExceptionStrings.NO_FILE_CHECK_PATH)
        else:
            return file_full_path


class FileService(BaseService):

    async def get_file_info(self, file_path: str) -> FileModel:
        name, extension, path = self.__file_path_to_attr(file_path)

        query = select(File).where(File.name == name, File.extension == extension, File.path == path)

        result = await self.db.execute_query(query)
        result = result.scalars().first()

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ExceptionStrings.NO_FILE_CHECK_PATH)

        return result

    async def upload_file(self, file: UploadFile, path: str = '/', comment: str | None = None,
                          exist_ok: bool = False) -> None:
        full_path = self.storage / path[1:]
        full_path.mkdir(parents=True, exist_ok=True)
        file_full_path = full_path / file.filename
        updated_at = None if not file_full_path.exists() else datetime.now()

        if file_full_path.exists() and not exist_ok:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ExceptionStrings.FILE_ALREADY_EXIST)

        with open(file_full_path, 'wb') as f:
            copyfileobj(file.file, f)

        file.file.close()

        file_info = {
            'name': file_full_path.stem,
            'extension': file_full_path.suffix,
            'size': file_full_path.stat().st_size,
            'path': path,
            'updated_at': updated_at,
            'comment': comment
        }

        if updated_at:
            stmt = (update(File).values(updated_at=updated_at).where(File.name == file_info['name'],
                                                                     File.extension == file_info['extension'],
                                                                     File.path == file_info['path']))
        else:
            stmt = insert(File).values(**file_info)

        await self.db.execute_stmt(stmt)

    async def delete_file(self, file_path: str) -> None:
        file_full_path = self.__check_file_exists(file_path)

        name, extension, path = self.__file_path_to_attr(file_path)
        stmt = delete(File).where(File.name == name, File.extension == extension, File.path == path)

        file_full_path.unlink()

        await self.db.execute_stmt(stmt)

    async def download_file(self, file_path: str) -> FileResponse:
        file_full_path = self.__check_file_exists(file_path)

        return FileResponse(file_full_path)

    async def update_file_info(self, file_path: str, new_name: str | None = None, new_path: str | None = None,
                               new_comment: str | None = None) -> None:
        full_file_path = self.__check_file_exists(file_path)

        file_info = await self.get_file_info(file_path)
        updated_at = datetime.now() if new_name or new_path or new_comment else file_info.updated_at
        new_name = new_name or file_info.name
        new_path = new_path or file_info.path
        new_comment = new_comment or file_info.comment

        new_full_path = self.storage / new_path[1:]

        new_full_path.mkdir(parents=True, exist_ok=True)

        full_file_path.replace(new_full_path / (new_name + file_info.extension))

        stmt = (update(File).values(name=new_name, path=new_path, comment=new_comment, updated_at=updated_at)
                .where(File.name == file_info['name'],
                       File.extension == file_info['extension'],
                       File.path == file_info['path']))

        await self.db.execute_stmt(stmt)


class StorageService(BaseService):

    async def get_all_files_infos(self) -> list[FileModel]:
        result = await self.db.execute_query(select(File))
        result = result.scalars().all()

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ExceptionStrings.NO_FILE_FOUND)

        return result

    async def get_files_infos_by_path(self, path: str = '/') -> list[FileModel]:
        query = select(File).where(File.path == path)
        result = await self.db.execute_query(query)
        result = result.scalars().all()

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ExceptionStrings.NO_FILE_CHECK_PATH)

        return result

    async def sync_db_with_storage(self) -> None:
        files_in_db = await self.db.execute_query(select(File))
        files_in_db = files_in_db.scalars().all() if files_in_db else []
        files_in_db = {Path(file.path) / (file.name + file.extension) for file in files_in_db}
        files_in_storage = set(self.storage.rglob('*.*'))

        for file in files_in_db:
            if self.storage / str(file)[1:] not in files_in_storage:
                name, extension, path = self.__file_path_to_attr(file)

                stmt = delete(File).where(File.name == name, File.extension == extension, File.path == path)
                await self.db.execute_stmt(stmt)

        files_in_db = {self.storage / str(file)[1:] for file in files_in_db}
        for file in files_in_storage:
            if file not in files_in_db:
                file_data = {
                    'name': file.stem,
                    'extension': file.suffix,
                    'size': file.stat().st_size,
                    'path': '/' if file.parent == self.storage else '/' + '/'.join(
                        file.parts[len(self.storage.parts):-1]) + '/'
                }
                stmt = insert(File).values(name=file_data['name'],
                                           extension=file_data['extension'],
                                           size=file_data['size'],
                                           path=file_data['path'])
                await self.db.execute_stmt(stmt)
