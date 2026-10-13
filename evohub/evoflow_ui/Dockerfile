FROM python:3.12-alpine

# git lets poetry fetch evoflow_db and evoflow_utils, which are git dependencies
# on this public repository.
RUN apk add --no-cache git poetry

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
COPY evoflow_ui ./evoflow_ui

RUN poetry install

EXPOSE 8181

CMD ["poetry", "run", "app"]
