








import os
import socket
import yaml
import time
import threading
from datetime import datetime
from fastapi import FastAPI
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

class HealthCheckService:
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        self.config_data = self.load_yaml_config()  # Load YAML once
        self.BASE_LOG_DIR = self.config_data.get("log_directory", "logs")
        self.last_health_check = {}  # Store the latest health check results
        self.start_background_health_check()  # Start periodic checks

    # Load YAML config only once at service start
    def load_yaml_config(self):
        with open(self.config_file, "r") as file:
            return yaml.safe_load(file)

    # Get timestamp
    def timestamp(self, fmt="%Y-%m-%d %H:%M:%S"):
        return datetime.now().strftime(fmt)

    # Create log file path
    def get_log_file(self, service_name, port, file):
        date_folder = self.timestamp("%Y-%m-%d")
        service_log_dir = os.path.join(self.BASE_LOG_DIR, service_name, date_folder)
        os.makedirs(service_log_dir, exist_ok=True)
        return os.path.join(service_log_dir, f"{port}_{file}.log")

    # Function to check a single port
    def check_port(self, host, service, servicename):
        port = service["port"]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)  # Reduced timeout
            result = s.connect_ex((host, int(port)))
            status = "UP" if result == 0 else "DOWN"
            service["status"] = status

            log_message = f"{self.timestamp()} | Service: {service['service']} | Port: {port} | Status: {status}"
            print(log_message)  # Print for real-time debugging
            
            # Log only if service is DOWN
            if status == "DOWN":
                log_file = self.get_log_file(servicename, port, service["service"])
                with open(log_file, "a") as f:
                    f.write(log_message + "\n")

        return {"service": service["service"], "port": port, "status": status}

    # Function to check all ports concurrently
    def check_ports_concurrently(self, host, services, servicename):
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda svc: self.check_port(host, svc, servicename), services))
        return results

    # Function to perform a fresh health check
    def get_latest_health_status(self):
        latest_health_status = {}

        for servicename, categories in self.config_data.items():
            if isinstance(categories, dict) and "local_host" in categories:
                host = categories["docker_host"] if os.path.exists("/.dockerenv") else categories["local_host"]
                
                latest_health_status[servicename] = {}
                for category, services in categories.items():
                    if isinstance(services, list):
                        latest_health_status[servicename][category] = self.check_ports_concurrently(host, services, servicename)

        return latest_health_status

    # Background health check function (Runs every 5 minutes)
    def perform_health_check(self):
        while True:
            self.last_health_check = self.get_latest_health_status()
            print(f"\n[{self.timestamp()}] Health check completed. Next check in 5 minutes...\n")
            time.sleep(300)  # Wait for 5 minutes

    # Start background thread for health checks
    def start_background_health_check(self):
        thread = threading.Thread(target=self.perform_health_check, daemon=True)
        thread.start()

# Instantiate the health check service
health_checker = HealthCheckService()

# API endpoint to get the latest health check result instantly
@app.get("/health-check")
def get_health_status():
    return health_checker.get_latest_health_status()  # Always fetch fresh data












# import os
# import socket
# import yaml
# import time
# import logging
# from datetime import datetime
# from fastapi import FastAPI
# from concurrent.futures import ThreadPoolExecutor

# app = FastAPI()

# # Load service configuration from YAML
# def load_yaml_config():
#     with open("config.yaml", "r") as file:
#         return yaml.safe_load(file)

# # Extract log directory from YAML
# config = load_yaml_config()
# BASE_LOG_DIR = config.get("log_directory", "logs")

# # Get timestamp
# def timestamp(fmt="%Y-%m-%d %H:%M:%S"):
#     return datetime.now().strftime(fmt)

# # Create a structured log directory and file
# def get_log_file(service_name, port, file):
#     date_folder = timestamp("%Y-%m-%d")
#     service_log_dir = os.path.join(BASE_LOG_DIR, service_name, date_folder)
#     os.makedirs(service_log_dir, exist_ok=True)
    
#     return os.path.join(service_log_dir, f"{port}_{file}.log")

# # Function to check a single port (optimized with timeout=0.5s)
# def check_port(host, service, servicename):
#     port = service["port"]
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.settimeout(0.5)  # Reduced timeout for faster checking
#         result = s.connect_ex((host, int(port)))
#         status = "UP" if result == 0 else "DOWN"
#         service["status"] = status

#         log_message = f"{timestamp()} | Service: {service['service']} | Port: {port} | Status: {status}"
#         print(log_message)  # Print for real-time debugging
        
#         # Log only if service is DOWN
#         if status == "DOWN":
#             log_file = get_log_file(servicename, port, service["service"])
#             with open(log_file, "a") as f:
#                 f.write(log_message + "\n")

#     return {"service": service["service"], "port": port, "status": status}

# # Function to check all ports concurrently using ThreadPoolExecutor
# def check_ports_concurrently(host, services, servicename):
#     with ThreadPoolExecutor(max_workers=10) as executor:  # Run up to 10 checks in parallel
#         results = list(executor.map(lambda svc: check_port(host, svc, servicename), services))
#     return results

# # Function to perform a fresh health check
# def get_latest_health_status():
#     latest_health_status = {}
#     config_data = load_yaml_config()  # Reload YAML in case of updates

#     for servicename, categories in config_data.items():
#         if isinstance(categories, dict) and "local_host" in categories:
#             host = categories["docker_host"] if os.path.exists("/.dockerenv") else categories["local_host"]
            
#             latest_health_status[servicename] = {}
#             for category, services in categories.items():
#                 if isinstance(services, list):  # Only process lists (ignoring 'host')
#                     latest_health_status[servicename][category] = check_ports_concurrently(host, services, servicename)

#     return latest_health_status

# # Background health check function (Runs every 5 minutes)
# def perform_health_check():
#     global last_health_check
#     while True:
#         last_health_check = get_latest_health_status()
#         print(f"\n[{timestamp()}] Health check completed. Next check in 5 minutes...\n")
#         time.sleep(300)  # Wait for 5 minutes

# # API endpoint to get the latest health check result instantly
# @app.get("/health-check")
# def get_health_status():
#     return get_latest_health_status()  # Fetch latest status when API is hit

# # Run health checks in the background when the API starts
# @app.on_event("startup")
# async def startup_event():
#     import threading
#     thread = threading.Thread(target=perform_health_check, daemon=True)
#     thread.start()
















# import os
# import socket
# import yaml
# import time
# import logging
# from datetime import datetime
# from fastapi import FastAPI

# app = FastAPI()


# # Load service configuration from YAML
# def load_yaml_config():
#     with open("config.yaml", "r") as file:
#         return yaml.safe_load(file)

# #Extract log directory from YAML
# config = load_yaml_config()
# BASE_LOG_DIR = config.get("log_directory", "logs") 


# # Get timestamp
# def timestamp(fmt="%Y-%m-%d %H:%M:%S"):
#     return datetime.now().strftime(fmt)

# # Create a structured log directory and file
# def get_log_file(service_name, port,file):
#     date_folder = timestamp("%Y-%m-%d")
#     time_stamp = timestamp("%H-%M-%S")
    
#     service_log_dir = os.path.join(BASE_LOG_DIR, service_name, date_folder)
#     os.makedirs(service_log_dir, exist_ok=True)
    
#     return os.path.join(service_log_dir, f"{port}_{file}_{time_stamp}.log")

# # Check if a port is open
# def check_ports(host, services,servicename):
#     for service in services:

        
#         port = service["port"]
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             s.settimeout(2)  # Timeout after 2 seconds
#             result = s.connect_ex((host, int(port)))  # Ensure port is an integer
#             status = "UP" if result == 0 else "DOWN"
#             service["status"] = status
            

#             log_message = f"{timestamp()} | Service: {service['service']} | Port: {port} | Status: {status}"
#             print(log_message)  # Optional: Print for real-time debugging
#             file=service['service']
            
#             # Log the health check status per service
#             if status == "DOWN":
#                 log_file = get_log_file(servicename, port,file)
#                 with open(log_file, "a") as f:
#                     f.write(log_message + "\n")

# # Health check function (Runs every 5 minutes)
# def perform_health_check():
#     global last_health_check
#     while True:
#         last_health_check = load_yaml_config()  # Reload YAML in case of updates

#         for servicename, categories in last_health_check.items():
#             if isinstance(categories, dict) and "local_host" in categories:
#                 if os.path.exists("/.dockerenv") or os.path.exists("/proc/self/cgroup"):
#                     host = categories["docker_host"]  # Running inside Docker
#                 else:
#                     host =categories["local_host"]   # Running locally

                
#                 for category, services in categories.items():
#                     if isinstance(services, list):  # Only process lists (ignoring 'host')
#                         check_ports(host, services,servicename)

#         print(f"\n[{timestamp()}] Health check completed. Next check in 5 minutes...\n")
#         time.sleep(300)  # Wait for 5 minutes




# # API endpoint to get the latest health check result
# @app.get("/health-check")
# def get_health_status():
#     return last_health_check

# # Run health checks in the background when the API starts
# @app.on_event("startup")
# async def startup_event():
#     import threading
#     thread = threading.Thread(target=perform_health_check, daemon=True)
#     thread.start()
