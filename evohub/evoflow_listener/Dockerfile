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
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install 

# Copy the rest of the application code into the container
COPY . .

# Run the Python script
CMD ["poetry", "run", "listen"]
