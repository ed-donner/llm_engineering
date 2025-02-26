FROM continuumio/miniconda3:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with sudo privileges
ARG USERNAME=llm_engineer
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Explicitly set bash as the default shell for the new user
RUN chsh -s /bin/bash $USERNAME

# Copy and create the custom environment
COPY environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml

# Set up conda for the new user
USER $USERNAME
RUN conda init bash

# Make sure the new user owns their home directory and has access to conda
USER root
RUN chown -R $USERNAME:$USERNAME /home/$USERNAME \
    && chown -R $USERNAME:$USERNAME /opt/conda/envs/codespace

# Switch back to the non-root user
USER $USERNAME
WORKDIR /home/$USERNAME

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]
