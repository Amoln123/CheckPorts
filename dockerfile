# Use the official Python image
FROM python:3.12

# Set the timezone
ENV TZ=Asia/Kolkata

# Install system dependencies for setting timezone
RUN apt-get update && apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Set the working directory
WORKDIR /app

# Copy the application files
COPY . .

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the required port
EXPOSE 6021

# Run the application using uvicorn
CMD ["uvicorn", "check_ports:app", "--host", "0.0.0.0", "--port", "6021", "--reload"]
