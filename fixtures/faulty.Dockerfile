FROM python:3.7.8

ARG version
ARG api_key=secret

ENV VERSION=$version

LABEL foo="bar bar bar"
LABEL maintainer="Fred"

LABEL foo="bar" maintainer="I, the author"

COPY credentials.txt config.py
COPY . b

COPY ../requirements.txt src/main.py /app/

ENV foo=bar
ENV NO_INT 1

# This is a comment
RUN apt-get \
    install curl && \
       git

RUN apt-get install --no-install-recommends curl && \
   git && \
    wget

SHELL ["powershell", "-command"]

EXPOSE 8000
EXPOSE 9000/tcp

ADD file_a file_a

USER me

WORKDIR /app

ENTRYPOINT ["python"]
# A comment
ONBUILD ADD c d

HEALTHCHECK CMD cat /tmp.txt

STOPSIGNAL 1337
STOPSIGNAL 1338

CMD ["python", "main.py", "--only-data"]

ARG api_key=secret
