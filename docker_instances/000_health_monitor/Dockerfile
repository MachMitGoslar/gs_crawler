FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt requirements.txt
COPY app.py app.py
COPY templates/ templates/

RUN python3 -m venv .venv
RUN .venv/bin/pip install -r requirements.txt

EXPOSE 5000

CMD [".venv/bin/python3", "app.py"]
