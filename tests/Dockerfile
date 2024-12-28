FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1  # Отключаем создание .pyc файлов
ENV PYTHONUNBUFFERED 1  # Убеждаемся, что вывод логов сразу идет в консоль (без буферизации)

WORKDIR /app
COPY tests/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY tests ./tests
COPY fastapi_crud_toolkit ./fastapi_crud_toolkit
COPY pyproject.toml .



ENTRYPOINT [ "/bin/sh", "-c", "pytest" ]