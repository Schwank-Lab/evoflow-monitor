# Use the official Python image from the Docker Hub
FROM python:3.11-alpine

# Install Poetry 
RUN apk add --no-cache poetry openssh

# Set the working directory in the container
WORKDIR /app

# Copy the rest of the application code into the container
COPY . .

#COPY pyproject.toml poetry.lock README.md ./

# Install dependencies
RUN poetry install 

# Run the Python script
CMD ["poetry", "run", "listen"]
