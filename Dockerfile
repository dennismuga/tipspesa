# Use python base image
FROM python:3.13-slim-bullseye

# Update packages, install uuidgen, and clean up
RUN apt-get update \
    && apt-get install -y uuid-runtime git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
#update pip & install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Set the timezone to Africa/Nairobi
RUN ln -sf /usr/share/zoneinfo/Africa/Nairobi /etc/localtime
