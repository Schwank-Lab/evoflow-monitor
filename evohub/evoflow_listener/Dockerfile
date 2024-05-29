# Use the official Python image from the Docker Hub
FROM python:3.12-alpine

# Install Poetry 
RUN apk add --no-cache \
    poetry

# Set the working directory in the container
WORKDIR /app

# Add README
RUN touch README.md

# Copy the Poetry lock file and the pyproject.toml
COPY evoflow_listener/pyproject.toml evoflow_listener/poetry.lock ./

# Copy depending packages
COPY db evoflow_utils  ./

# Install dependencies
RUN poetry install 

# Copy the rest of the application code into the container
COPY evoflow_listener/. .

# Run the Python script
CMD ["poetry", "run", "listen"]
