# Use official Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . .

# Expose the port your app runs on (change if needed)
EXPOSE 8000

# Run your app (change main.py to your entrypoint if different)
CMD ["python", "main.py"]
