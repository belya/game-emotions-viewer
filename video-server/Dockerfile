FROM python:3.8

USER root

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

WORKDIR /opt/mqtt-server

COPY ./requirements.txt ./ 
RUN pip install --no-cache-dir -r ./requirements.txt

COPY ./devices.json ./

CMD python ./server.py