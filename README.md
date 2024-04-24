# test_work
Тестовое задание для вакансии на Python Backend Developer.

## _Установка и запуск_ _(проверено на macOS)_
Воспользоваться приложением можно следуя следующей инструкции:
1. Установить Python 3.12
2. Скопировать файлы проекта в папку
3. Запустить терминал из этой папки
4. Выполнить `docker compose -f docker-compose-local.yml up` для запуска базы данных
5. Запустить ещё один терминал из папки проекта и выполнить:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
   - `alembic upgrade head`
   - `uvicorn src.main:app --reload --host 127.0.0.1 --port 8000`

Либо запустить с помощью Docker:
   - Открыть терминал из папки проекта
   - Выполнить сборку контейнера `docker compose up`

## _Настройка_
При необходимости в файле конфигурации окружения `.evn` можно изменить:
   - путь к хранилищу `STORAGE_PATH`
   - путь к его volume `DOCKER_PATH` в контейнере
   - опцию `docker` для правильной работы при запуске всего проекта в Docker

## _Использование_
Для тестирования функций приложения можно открыть [автоматическую интерактивную документацию](http://127.0.0.1:8000/docs#).
### ****Доступные функции:****
* Получение списка информации о всех файлах: [`Get All Files Infos`](http://127.0.0.1:8000/docs#/file/get_all_files_infos_files__get)
* Получение информации о конкретном файле по его пути в хранилище: [`Get File Info`](http://127.0.0.1:8000/docs#/file/get_file_info_files_file_get)
* Добавление файла (или замена с обновлением, если он уже существует и параметр `exist_ok==False`): [`Upload File`](http://127.0.0.1:8000/docs#/file/upload_file_files_upload_post)
* Удаление файла: [`Delete File`](http://127.0.0.1:8000/docs#/file/delete_file_files_delete_delete)
* Получение информации о файлах, находящихся по определённому пути: [`Get Files Infos By Path`](http://127.0.0.1:8000/docs#/file/get_files_infos_by_path_files_path_get)
* Загрузка файла: [`Download File`](http://127.0.0.1:8000/docs#/file/download_file_files_download_get)
* Обновление информации о файле: [`Update File Info`](http://127.0.0.1:8000/docs#/file/update_file_info_files_update_patch)
* Синхронизация информации в базе данных на основе состояния хранилища: [`Sync Db With Storage`](http://127.0.0.1:8000/docs#/file/sync_db_with_storage_files_sync_get)
