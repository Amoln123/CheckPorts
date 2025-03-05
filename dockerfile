# Use a lightweight Python image as the base
FROM python:3.12-slim AS builder

# Set the timezone
ENV TZ=Asia/Kolkata
WORKDIR /app

# Install pip and dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir uvicorn  # Ensure uvicorn is installed

# Copy application source code
COPY . .

# Compile Python files to bytecode (.pyc) and delete source files
RUN python -m compileall -b .
RUN find . -type f -name "*.py" -delete

# Create a smaller final image
FROM python:3.12-slim

WORKDIR /app

# Copy only the compiled Python files (.pyc) from the builder stage
COPY --from=builder /app /app

# Reinstall `uvicorn` in the final stage to ensure it exists in PATH
RUN pip install --no-cache-dir uvicorn fastapi PyYAML

# Set a non-root user for security
RUN groupadd -g 1000 appuser && useradd -m -u 1000 -g appuser appuser
USER appuser

# Expose the FastAPI port
EXPOSE 6021

# Run the FastAPI application
CMD ["uvicorn", "check_ports:app", "--host", "0.0.0.0", "--port", "6021"]
