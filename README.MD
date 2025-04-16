# Backend на django-rest-framework
## Часть с user service
USER SERVICE часть backend'a на FastAPI: https://github.com/pOsdas/FastAPI-backend переписанная на django и DRF
> На столько, на сколько это возможно

- Первая часть: https://github.com/pOsdas/Django-backend-1part

Асинхронный запуск с использованием uvicorn:
```shell
poetry run uvicorn user_app_project.asgi:application --host 127.0.0.1 --port 8006 --reload
```
