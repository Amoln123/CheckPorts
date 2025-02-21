# Use the official Python image
FROM python:3.12

# Set the timezone (adjust if needed)
ENV TZ=Asia/Kolkata

# Install system dependencies for setting timezone
RUN apt-get update && apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Set the working directory
WORKDIR /app

# Copy the application code to the container
COPY . .

# Ensure no conflicting yaml.py file exists
RUN rm -f /app/yaml.py

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Ensure the script is executable
RUN chmod +x check_ports.py

# Run the script
CMD ["python", "check_ports.py"]
