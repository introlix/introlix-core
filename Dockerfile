FROM python:3.10

RUN useradd -m -u 1000 user

WORKDIR /app

COPY --chown=user . /app

RUN pip install -r requirements.txt

RUN mkdir -p /app/logs
RUN chmod 777 /app/logs

# Copy the shell script into the container
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Use the shell script to start both processes
CMD ["/bin/bash", "/app/start.sh"]