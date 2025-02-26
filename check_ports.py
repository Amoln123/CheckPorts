import os
import socket
import yaml
import time
import logging
from datetime import datetime
from fastapi import FastAPI

app = FastAPI()


# Load service configuration from YAML
def load_yaml_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

#Extract log directory from YAML
config = load_yaml_config()
BASE_LOG_DIR = config.get("log_directory", "logs") 


# Get timestamp
def timestamp(fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.now().strftime(fmt)

# Create a structured log directory and file
def get_log_file(service_name, port,file):
    date_folder = timestamp("%Y-%m-%d")
    time_stamp = timestamp("%H-%M-%S")
    
    service_log_dir = os.path.join(BASE_LOG_DIR, service_name, date_folder)
    os.makedirs(service_log_dir, exist_ok=True)
    
    return os.path.join(service_log_dir, f"{port}_{file}_{time_stamp}.log")

# Check if a port is open
def check_ports(host, services,servicename):
    for service in services:

        
        port = service["port"]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)  # Timeout after 2 seconds
            result = s.connect_ex((host, int(port)))  # Ensure port is an integer
            status = "UP" if result == 0 else "DOWN"
            service["status"] = status
            

            log_message = f"{timestamp()} | Service: {service['service']} | Port: {port} | Status: {status}"
            print(log_message)  # Optional: Print for real-time debugging
            file=service['service']
            
            # Log the health check status per service
            if status == "DOWN":
                log_file = get_log_file(servicename, port,file)
                with open(log_file, "a") as f:
                    f.write(log_message + "\n")

# Health check function (Runs every 5 minutes)
def perform_health_check():
    global last_health_check
    while True:
        last_health_check = load_yaml_config()  # Reload YAML in case of updates

        for servicename, categories in last_health_check.items():
            if isinstance(categories, dict) and "host" in categories:
                host = categories["host"]  # Get the specific host for this service
                
                for category, services in categories.items():
                    if isinstance(services, list):  # Only process lists (ignoring 'host')
                        check_ports(host, services,servicename)

        print(f"\n[{timestamp()}] Health check completed. Next check in 5 minutes...\n")
        time.sleep(300)  # Wait for 5 minutes




# API endpoint to get the latest health check result
@app.get("/health-check")
def get_health_status():
    return last_health_check

# Run health checks in the background when the API starts
@app.on_event("startup")
async def startup_event():
    import threading
    thread = threading.Thread(target=perform_health_check, daemon=True)
    thread.start()
