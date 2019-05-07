FROM python:3.6.8-stretch

EXPOSE 80

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN apt-get update
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /app