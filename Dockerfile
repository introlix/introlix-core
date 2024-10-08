# Use the official Python 3.10.9 image
FROM python:3.10.9

# Copy the current directory contents into the container at /app
COPY . /app

# Set the working directory to /app
WORKDIR /app

# Install the dependencies from requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Expose port 7860 (default Hugging Face Space port)
EXPOSE 7860

# Start the FastAPI app (adjust the path to your FastAPI app file)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
