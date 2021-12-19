# This file is only needed if you need to create your own Reach container image.
# A pre-built image is available in Docker.io: https://hub.docker.com/repository/docker/randyoyarzabal/reach
# via the command: $> docker pull randyoyarzabal/reach:latest
#
# HOW TO USE THIS FILE
# 
# While in the same directory as this file...
#
# Build Container:
# $> docker build -t randyoyarzabal/reach .
#
# Using the Container:
# In your startup file somewhere:
#   - export REACH_PATH=<local path of reach>
#
# Option 1:
# Ad-hoc (easy way):
#   - $> docker run --rm -it -v $REACH_PATH:/reach randyoyarzabal/reach reach.py
#
# Option 2:
# Run container in background once:
#   - $> docker run --rm -d -it -v $REACH_PATH:/reach --name=reach randyoyarzabal/reach
# Execute reach:
#   - $> docker exec -it reach reach.py

# This is a multi-stage build file that significantly minimizes the container image size.

# Stage 1
FROM python:3.9-slim AS compile-image

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel;

# Ignore versions
# RUN cat requirements.txt | cut -d'=' -f 1 | xargs pip install --upgrade;

# Adhere to versions defined.
RUN pip install -r requirements.txt

# Stage 2
FROM python:3.9-slim AS build-image
ENV REACH_PATH="/reach"
ENV PATH="/opt/venv/bin:$REACH_PATH:$PATH"

WORKDIR $REACH_PATH

COPY --from=compile-image /opt/venv /opt/venv
COPY . $REACH_PATH