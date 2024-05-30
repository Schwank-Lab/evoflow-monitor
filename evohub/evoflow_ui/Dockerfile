# Use the official Python image from the Docker Hub
FROM python:3.12-alpine

# Install Poetry 
RUN apk add --no-cache poetry openssh

# Set the working directory in the container
WORKDIR /app

# Copy the Poetry lock file and the pyproject.toml
COPY pyproject.toml poetry.lock README.md evoflow_ui ./

# Install dependencies
RUN poetry install 

# Run the Python script
CMD ["poetry", "run", "app"]