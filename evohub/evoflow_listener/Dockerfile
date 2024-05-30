FROM idec_base:latest

# Set the working directory in the container
WORKDIR /app

COPY pyproject.toml poetry.lock README.md evoflow_listener ./

# Install dependencies
RUN eval "$(ssh-agent -s)" && \
    ssh-add /root/.ssh/idec_github && \
    poetry install
    
# Run the Python script
CMD ["poetry", "run", "listen"]






