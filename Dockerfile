FROM python:3.10

# Create a non-root user
RUN useradd -m -u 1000 user

WORKDIR /app

# Copy files and set ownership to the user
COPY --chown=user . /app

# Install dependencies
RUN pip install -r requirements.txt

# Create logs directory with more restrictive permissions
RUN mkdir -p /app/logs
RUN chmod 755 /app/logs

# Copy and make the shell script executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Switch to the non-root user
USER user

# Run the shell script
CMD ["/bin/bash", "/app/start.sh"]
