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

# Create .env file with placeholder for OPENAI_API_KEY
RUN echo 'OPENAI_API_KEY=XXX' > /home/jovyan/.env && \
    # activate conda environment and set it as default
    echo 'conda activate llms' >> /home/jovyan/.bashrc
