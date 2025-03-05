#check_ports.py
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
        # self.BASE_LOG_DIR = self.config_data.get("log_directory", "logs")
        self.BASE_LOG_DIR = self.config_data.get("log_directory", "/tmp/logs")
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





