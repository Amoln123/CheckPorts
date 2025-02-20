# Use official Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy script and configuration file
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir pyyaml

# Ensure logs directory exists
RUN mkdir -p /app/logs

# Start the script
CMD ["python", "check_ports.py"]
