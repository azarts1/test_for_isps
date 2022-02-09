import asyncio
import os
import shutil
import tarfile
from stat import S_ISDIR

from aiohttp import ClientSession, ClientResponse

from base import SingletonStateFiles
from base.utils import close_session


class LoadingFile:
    def __init__(self, file_name_archive_: str, file_name_: str, client_: ClientSession, session_: ClientResponse):
        self.state = SingletonStateFiles()
        self.file_name_archive = file_name_archive_
        self.file_name = file_name_
        self.client = client_
        self.session = session_
        self.file_path = self.state.storage_path + self.file_name
        self.file_path_archive = self.state.storage_path + self.file_name_archive

    async def loading(self) -> None:
        await self._download_archive()
        #   теперь нам не нужно подключение
        await close_session(self.client, self.session)

        await self._unpacking()
        self.state.update_state_files(file_name=self.file_name_archive,
                                      file_path=self.file_path_archive, status_file='ok')

        self.state.update_state_files(file_name=self.file_name,
                                      file_path=self.file_path, status_file='ok')

    async def _download_archive(self) -> None:
        #   получаем количество данных для процента
        content_length = self.session.content_length / 1024 * 1024
        f = open(self.file_path_archive, mode='wb')
        count_for_process = int()
        while True:
            #   по килобайту вытягиваем данные
            bdata_file_zip = await self.session.content.read(1024)
            if not bdata_file_zip:
                break
            #   пишем в файл
            f.write(bdata_file_zip)

            count_for_process = count_for_process + 1024
            #   обновляем статус
            process = int((count_for_process / content_length) * 100)
            self.state.update_state_files(file_name=self.file_name_archive, file_path=self.file_path_archive,
                                          status_file='downloading', process=process)
        f.close()

    async def _unpacking(self) -> None:
        tgfile = tarfile.open(name=self.file_path_archive)
        file_in_th = tgfile.getnames()
        count_file_in_tg = len(file_in_th)
        #   создаем папку
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)
        for count, file in enumerate(file_in_th):
            #   получаем процент
            process = int((count / count_file_in_tg) * 100)
            self.state.update_state_files(file_name=self.file_name_archive, file_path=self.file_path_archive,
                                          status_file='unpacking', process=process)
            tgfile.extract(file, self.file_path)

            #   поддерживаем асинхронность
            await asyncio.sleep(0)


async def delete_archive(file_name: str) -> None:
    storage = SingletonStateFiles()
    file_info = os.stat(storage.storage_path + file_name).st_mode

    #   удаляем с машины
    if S_ISDIR(file_info):
        shutil.rmtree(storage.storage_path + file_name)
    else:
        os.remove(storage.storage_path + file_name)

    #   удаляем из статусаведенья
    storage.delete_state_file(file_name)
