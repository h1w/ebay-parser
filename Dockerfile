FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update -y && \
    apt install -y python3-dev \
    gcc \
    musl-dev

ADD pyproject.toml /app

RUN pip install --upgrade pip
RUN pip install poetry

RUN touch README.md
RUN poetry config virtualenvs.create false
RUN poetry install

COPY /app/* /app/app/

ENTRYPOINT ["poetry", "run", "python", "-m", "app"]
