import os

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from archive.controller import route_archive
from base import SingletonStateFiles

app = FastAPI()
#   сраза инициализируем статусы файлов
SingletonStateFiles()

app.include_router(route_archive)

if os.getenv("DEBUG") == '0' or os.getenv("DEBUG") is None and os.getenv("AU_KEY") is None:
    #   проверяем авторизацию
    @app.middleware("http")
    async def catch_exceptions_middleware(request: Request, call_next):
        if au := request.headers.get('authorize'):
            if au == os.getenv("AU_KEY"):
                return await call_next(request)
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=dict(detail=dict(
            error='Без авторизации никак')))
