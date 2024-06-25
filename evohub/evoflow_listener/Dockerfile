FROM idec_base:latest

# Set the working directory in the container
WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./

#COPY evoflow_listener ./evoflow_listener

# Install dependencies
RUN eval "$(ssh-agent -s)" && \
    ssh-add /root/.ssh/idec_github && \
    poetry install --no-root

RUN tree

# Run the Python script
CMD ["poetry", "run", "listen"]






