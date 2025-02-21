# Use the official Python image
FROM python:3.12

# Set the timezone (change to your required timezone)
ENV TZ=Asia/Kolkata

# Install system dependencies for setting timezone
RUN apt-get update && apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Set the working directory
WORKDIR /app

# Copy the script and YAML config file
COPY . .

# Install required Python packages
RUN pip install --no-cache-dir pyyaml

# Set the command to run the script
CMD ["python", "check_ports.py"]
