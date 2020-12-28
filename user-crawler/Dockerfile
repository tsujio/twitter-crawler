FROM python:3

RUN apt update -y

RUN apt install -y sqlite3

COPY ./main.py /app/main.py
COPY ./lib /app/lib

RUN mkdir -p /app/data

CMD ["bash"]
