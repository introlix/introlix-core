# Use the official Python image as the base image
FROM python:3.10.9 AS build

# Set the working directory
WORKDIR /app

# Copy only requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code
COPY . .

# Use a smaller base image for the final image
FROM python:3.10.9-slim

# Set the working directory
WORKDIR /app

# Copy installed dependencies from the build stage
COPY --from=build /app /app

# Expose port 7860
EXPOSE 7860

# Start the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
