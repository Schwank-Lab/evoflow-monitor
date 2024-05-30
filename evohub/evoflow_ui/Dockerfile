# Use the official Python image from the Docker Hub
FROM python:3.12-alpine

# Install Poetry 
RUN apk add --no-cache poetry openssh

# set up ssh
RUN mkdir -p /root/.ssh \
    # only this user should be able to read this folder (it may contain private keys)
    && chmod 0700 /root/.ssh \
    # unlock the user
    && passwd -u root

# paste ssh key
ARG ssh_pub_key

RUN echo "$ssh_pub_key" > /root/.ssh/authorized_keys

# Set the working directory in the container
WORKDIR /app

# Copy the Poetry lock file and the pyproject.toml
COPY pyproject.toml poetry.lock README.md evoflow_ui ./

# Install dependencies
RUN poetry install 

# Run the Python script
CMD ["poetry", "run", "app"]