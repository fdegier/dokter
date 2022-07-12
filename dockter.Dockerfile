FROM python:3.10

WORKDIR /app

COPY dist dist

RUN pip install dist/dockter-*.tar.gz && rm -rf dist

