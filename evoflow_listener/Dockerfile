# Use the official Python image from the Docker Hub
# FROM python:3.11.5-slim-bookworm
FROM python:3.11.5-alpine

# Install Poetry dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    make


# Install Poetry
RUN pip install poetry

# Set the working directory in the container
WORKDIR /app

# Copy the Poetry lock file and the pyproject.toml
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev


# Copy the rest of the application code into the container
COPY . .

# Run the Python script
CMD ["poetry", "run", "python", "-u", "evoflow_listener/mqtt_listener.py"]
CMD ["sh"]
