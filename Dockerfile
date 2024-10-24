FROM python:3.10

RUN useradd -m -u 1000 user

WORKDIR /app

COPY --chown=user . /app

RUN pip install -r requirements.txt

RUN mkdir -p /app/logs
RUN chmod 777 /app/logs

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]