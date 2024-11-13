# Use an official Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the folders into the container
COPY src /app/src
COPY out /app/out
COPY dot_examples /app/dot_examples
COPY batchscripts /app/batchscripts

RUN cd src

# Run bash as the default command
CMD ["/bin/bash"]
