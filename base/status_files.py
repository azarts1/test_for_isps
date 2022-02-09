import os
from os import listdir
from stat import S_ISDIR


class SingletonStateFiles:
    state_files = dict()
    storage_path = str()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SingletonStateFiles, cls).__new__(cls)
            #   загружаем основыне данные при инициализации объекта
            cls.instance.load_storage_path()
            cls.instance.load_state_files()
        return cls.instance

    def load_storage_path(self) -> None:
        if storage_path_ := os.getenv("storege_path"):
            self.storage_path = storage_path_
        else:
            self.storage_path = os.getcwd() + '/storage/'

    def load_state_files(self) -> None:
        file_storage = {f for f in os.listdir(self.storage_path)}
        for file in file_storage:
            self.update_state_files(file, self.storage_path + file, 'ok')

    def update_state_files(self, file_name: str, file_path: str, status_file: str, process: int | None = None) -> None:
        update_data = {
            "status": status_file, "file_path": file_path
        }
        if process is not None:
            update_data.update(process=process)
        #   если статус ок то заполняем данные о данных внути
        if status_file == 'ok':

            file_info = os.stat(self.storage_path + file_name).st_mode
            if S_ISDIR(file_info):
                all_files_dir = [f for f in listdir(file_path)]
                update_data.update(files={file_name: all_files_dir})
            else:
                update_data.update(files=file_name)
        self.state_files.update({file_name: update_data})

    def delete_state_file(self, file_path: str) -> None:
        #   удаляем ссылку
        self.get_state_file(file_path).clear()

    def get_state_file(self, file_path: str) -> dict:
        return self.state_files.get(file_path)
