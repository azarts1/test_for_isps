import asyncio
import os


import aiohttp
from fastapi import status, APIRouter, HTTPException
from fastapi.responses import JSONResponse

from base import SingletonStateFiles, LoadingFile, delete_archive
from base.utils import close_session
from archive.models import ArchiveUrl

route_archive = APIRouter(prefix='/archive', tags=['archive'])


#   не стал выносить отдельно тк тут HTTPException, а это все же логика хендлера
def check_valid_file_name(file_name) -> tuple[str, str] | HTTPException:
    file_storage = {f for f in os.listdir(SingletonStateFiles().storage_path)}
    #   проверка на слеши, дериктории не тестились, так что они ни к чему хорошему
    if file_name.find('/') != -1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=dict(
            error='Осуждаем слеши'))
    #   переименнововать файл тоже не будем, пусть в другой стороны этим занимаются
    if file_name in file_storage:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=dict(
            error='Файл с таким имем уже есть, path_name в помощь'))
    #   проверяем название, если нет указания архива, добавляем
    if file_name[7:].find('.tar.gz') == -1:
        file_name_archive = file_name + '.tar.gz'
    else:
        file_name_archive = file_name
        file_name = (file_name_archive[::-1].replace('.tar.gz'[::-1], '', 1))[::-1]
    return file_name_archive, file_name


@route_archive.post('/')
async def archive_downland(data: ArchiveUrl) -> JSONResponse | HTTPException:
    file_name_archive, file_name = check_valid_file_name(data.url.split('/')[-1]) if not data.file_name \
        else check_valid_file_name(data.file_name)

    client = None
    session = None
    try:
        #   создаем клинта
        client = await aiohttp.ClientSession().__aenter__()
        #   получаем данные с сайта
        session = await client.get(data.url).__aenter__()
        if session.status == 200 and session.content_type == 'application/octet-stream':
            #   если все отлично созадаем объек который занимается загрукой данных
            load_file = LoadingFile(file_name_archive, file_name, client, session)

            #   получаем текущий увентлуп
            loop = asyncio.get_running_loop()
            #   запускаем в него задачу на работу с файлом
            loop.create_task(load_file.loading())

            return JSONResponse(status_code=status.HTTP_200_OK, content=dict(archive_id=file_name_archive,
                                                                             unarchive_id=file_name))
        else:
            await close_session(client, session)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=dict(
                error='Ссылка куда-то не туда'))

    except aiohttp.InvalidURL:
        await close_session(client, session)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=dict(
            error='Не очень похоже на ссылку'))


@route_archive.get('/{id}')
async def archive_status(id) -> JSONResponse | HTTPException:
    state_file = SingletonStateFiles()
    content = state_file.get_state_file(id)
    if content:
        return JSONResponse(status_code=status.HTTP_200_OK, content=content)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@route_archive.delete('/{id}')
async def delete_file(id) -> HTTPException | JSONResponse:
    state_file = SingletonStateFiles()
    #   получаем состояние файла
    if file_status := state_file.get_state_file(id):
        if file_status['status'] == 'ok':
            loop = asyncio.get_running_loop()
            #   удаляем если что хорошо
            loop.create_task(delete_archive(id))
            return JSONResponse(status_code=status.HTTP_200_OK)
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=dict(
                error='С файлом проводятся работы'))
    else:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=dict(
            error='Файл не найден'))
