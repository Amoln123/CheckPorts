import socket
import yaml
import time
import os
from datetime import datetime

# Get current timestamp
def timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

# Generate log filename with timestamp
def get_log_filename():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)  # Ensure the logs directory exists
    log_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(log_dir, f"down_log_{log_time}.log")

# Load YAML config
def load_config(file="config.yaml"):
    with open(file, "r", encoding="utf-8") as f:  # Ensure YAML file is read in UTF-8
        return yaml.safe_load(f)

# Function to check port status and log if down
def check_ports(host, ports_dict, category, log_file):
    log_entries = []
    
    for port in ports_dict:
        service_name = ports_dict[port]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)  # Timeout after 2 seconds
            result = s.connect_ex((host, int(port)))  # Ensure port is an integer
            status = "✅ UP" if result == 0 else "❌ DOWN"
            log_entry = f"{timestamp()} {status} {service_name} [{category}] on port {port}"
            print(log_entry)
            
            # If service is DOWN, log the entry
            if result != 0:
                log_entries.append(log_entry)
    
    # Write to log file if there are any DOWN services
    if log_entries:
        with open(log_file, "a", encoding="utf-8") as f:  # Fix: UTF-8 encoding
            f.write("\n".join(log_entries) + "\n")

if __name__ == "__main__":
    while True:  # Infinite loop to check every 5 minutes
        config = load_config()

        if os.path.exists("/.dockerenv") or os.path.exists("/proc/self/cgroup"):
            host = config["mongo"]["dockerhost"] # Running inside Docker
        else:
            host = config["mongo"]["localhost"] # Running locally 

      


        log_file = get_log_filename()  # Generate a new log file on each check

        print("\n--- Checking Services Status ---")
        check_ports(host, config["mongo"]["mongoports"], "MongoDB", log_file)
        check_ports(host, config["mongo"]["servicesports"], "Service", log_file)
        check_ports(host, config["mongo"]["redisinduports"], "ConfigRedis", log_file)
        check_ports(host, config["mongo"]["redisclusterports"], "RequestRedis Cluster", log_file)

        print(f"\n--- Next check in 5 minutes... ---\n")
        time.sleep(60)  # Wait for 5 minutes (300 seconds)
