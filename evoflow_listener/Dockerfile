# Use the official Python image from the Docker Hub
FROM python:3.11.5-slim-bookworm

# Install Poetry
RUN pip install poetry

# Set the working directory in the container
WORKDIR /app

# Copy the Poetry lock file and the pyproject.toml
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy the rest of the application code into the container
COPY . .

# Run the Python script
CMD ["poetry", "run", "python", "evoflow_listener/mqtt_listener.py"]
