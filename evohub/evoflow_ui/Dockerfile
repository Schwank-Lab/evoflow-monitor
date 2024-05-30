FROM idec_base:latest

# Set the working directory in the container
WORKDIR /app

# Copy the Poetry lock file and the pyproject.toml
COPY pyproject.toml poetry.lock README.md evoflow_ui ./

# Install dependencies
RUN eval "$(ssh-agent -s)" && \
    ssh-add /root/.ssh/idec_github && \
    poetry install

# Run the Python script
CMD ["poetry", "run", "app"]
