# Use the official Python image from the Docker Hub
FROM python:3.12-alpine

# Install openssh
RUN apk add --no-cache openssh poetry

RUN echo poetry --version

# Set up ssh
RUN mkdir -p /root/.ssh \
    && chmod 0700 /root/.ssh

# Paste ssh key
ARG ssh_private_key
RUN echo "$ssh_private_key" > /root/.ssh/idec_github \
    && chmod 600 /root/.ssh/idec_github

RUN echo "SSH Key Content:" \
    && cat /root/.ssh/idec_github

# Configure ssh for GitHub
RUN echo "Host *.github.com" >> /root/.ssh/config
RUN echo "    AddKeysToAgent yes" >> /root/.ssh/config
RUN echo "    IdentityFile /root/.ssh/idec_github" >> /root/.ssh/config
RUN echo "    StrictHostKeyChecking no" >> /root/.ssh/config
RUN chmod 600 /root/.ssh/config

# Add GitHub to known hosts
RUN touch /root/.ssh/known_hosts \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts

# Test ssh connection to GitHub
RUN eval "$(ssh-agent -s)" && \
    ssh-add /root/.ssh/idec_github
