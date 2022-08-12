FROM python:3.10.5-alpine

WORKDIR /app
RUN apk add bash openssh curl git

COPY dist dist

RUN pip install dist/dokter-*.tar.gz && rm -rf dist

COPY create-mr.sh /
