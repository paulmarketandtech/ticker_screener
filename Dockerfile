FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
COPY counter.txt /app/
COPY selected_room.json /app/
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN mkdir -p /logs

CMD ["python", "app/cjt_ticker.py"]