FROM jupyter/datascience-notebook

USER root
RUN apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends vim && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt
USER jovyan

# Install mamba and create conda environment
RUN conda install -y mamba -n base -c conda-forge

# Copy environment file and create conda environment
COPY environment.yml /tmp/environment.yml
RUN mamba env create -f /tmp/environment.yml

# Activate conda environment and set it as default
RUN echo 'conda activate llms' >> /home/jovyan/.bashrc
