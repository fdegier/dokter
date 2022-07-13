FROM python:3.10.5-alpine

WORKDIR /app

COPY dist dist

RUN pip install dist/dockter-*.tar.gz && rm -rf dist

USER nobody
