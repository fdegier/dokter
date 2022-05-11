import pytest

from src.parser import DockerfileParser


@pytest.mark.parametrize(
    "raw,image,version",
    [
        ("FROM python3.8", "python3.8", None),
        ("FROM python:3.8.9", "python", "3.8.9"),
        ("FROM ruby:latest", "ruby", "latest")
    ]
)
def test_froms(raw, image, version):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.froms) == 1
    from_details = dfp.froms[0]["instruction_details"]
    assert from_details["image"] == image
    assert from_details.get("version") == version


@pytest.mark.parametrize(
    "raw,comment",
    [
        ("#This is a comment", "This is a comment"),
        ("# This is also a comment", "This is also a comment")
    ]
)
def test_comments(raw, comment):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.comments) == 1
    assert dfp.comments[0]["instruction"] == "COMMENT"
    assert dfp.comments[0]["instruction_details"].get("comment") == comment


@pytest.mark.parametrize(
    "raw,user,group",
    [
        ("USER root", "root", None),
        ("USER 1000:1234", "1000", "1234")
    ]
)
def test_users(raw, user, group):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.users) == 1
    assert dfp.users[0]["instruction"] == "USER"
    assert dfp.users[0]["instruction_details"].get("user") == user
    assert dfp.users[0]["instruction_details"].get("group") == group


@pytest.mark.parametrize(
    "raw,chown,source,target",
    [
        ("COPY . .", None, ".", "."),
        ("COPY --chown=me:me . /app", "me:me", ".", "/app"),
        ("COPY --chown=1000:1234 app /app/app", "1000:1234", "app", "/app/app"),
        ("COPY app .", None, "app", "."),
    ]
)
def test_copies(raw, chown, source, target):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.copies) == 1
    assert dfp.copies[0]["instruction"] == "COPY"
    assert dfp.copies[0]["instruction_details"].get("chown") == chown
    assert dfp.copies[0]["instruction_details"].get("source") == source
    assert dfp.copies[0]["instruction_details"].get("target") == target


@pytest.mark.parametrize(
    "raw,chown,source,target",
    [
        ("ADD . .", None, ".", "."),
        ("ADD --chown=me:me . /app", "me:me", ".", "/app"),
        ("ADD --chown=1000:1234 app /app/app", "1000:1234", "app", "/app/app"),
        ("ADD app .", None, "app", "."),
    ]
)
def test_adds(raw, chown, source, target):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.adds) == 1
    assert dfp.adds[0]["instruction"] == "ADD"
    assert dfp.adds[0]["instruction_details"].get("chown") == chown
    assert dfp.adds[0]["instruction_details"].get("source") == source
    assert dfp.adds[0]["instruction_details"].get("target") == target


def test_instructions():
    dfp = DockerfileParser("../Dockerfile")
    assert len(dfp.instructions) == 27
    instructions = ['FROM', 'ARG', 'ARG', 'ENV', 'LABEL', 'LABEL', 'LABEL', 'COPY', 'COPY', 'COPY', 'ENV', 'ENV',
                    'COMMENT', 'RUN', 'RUN', 'SHELL', 'EXPOSE', 'EXPOSE', 'ADD', 'USER', 'WORKDIR', 'ENTRYPOINT',
                    'ONBUILD', 'HEALTHCHECK', 'STOPSIGNAL', 'STOPSIGNAL', 'CMD']
    assert dfp.instructions == instructions


@pytest.mark.parametrize(
    "raw,argument,default_value",
    [
        ("ARG version", "version", None),
        ("ARG api_key=secret", "api_key", "secret")
    ]
)
def test_args(raw, argument, default_value):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.args) == 1
    assert dfp.args[0]["instruction"] == "ARG"
    assert dfp.args[0]["instruction_details"].get("argument") == argument
    assert dfp.args[0]["instruction_details"].get("default_value") == default_value


@pytest.mark.parametrize(
    "raw,environment_variable,default_value",
    [
        ("ENV VERSION=$version", "VERSION", "$version"),
        ("ENV DEBIAN_FRONTEND=noninteractive", "DEBIAN_FRONTEND", "noninteractive")
    ]
)
def test_envs(raw, environment_variable, default_value):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.envs) == 1
    assert dfp.envs[0]["instruction"] == "ENV"
    assert dfp.envs[0]["instruction_details"].get("environment_variable") == environment_variable
    assert dfp.envs[0]["instruction_details"].get("default_value") == default_value


@pytest.mark.parametrize(
    "raw,key,value,raw_labels",
    [
        ("LABEL maintainer='me'", "maintainer", "me", None),
        ('LABEL maintainer="me"', "maintainer", "me", None),
        ('LABEL maintainer=me', "maintainer", "me", None),
        ("LABEL maintainer='me' version='0.1.1'", None, None, "maintainer='me' version='0.1.1'")
    ]
)
def test_labels(raw, key, value, raw_labels):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.labels) == 1
    assert dfp.labels[0]["instruction"] == "LABEL"
    assert dfp.labels[0]["instruction_details"].get("key") == key
    assert dfp.labels[0]["instruction_details"].get("value") == value
    assert dfp.labels[0]["instruction_details"].get("raw_labels") == raw_labels


@pytest.mark.parametrize(
    "raw,executable,arguments",
    [
        ("RUN apt-get install curl && git", "apt-get", "install curl && git"),
        ("""RUN apt-get \\
                install curl && \\
                git""", "apt-get", "\\               install curl && \\               git")
    ]
)
def test_runs(raw, executable, arguments):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.runs) == 1
    assert dfp.runs[0]["instruction"] == "RUN"
    assert dfp.runs[0]["instruction_details"].get("executable") == executable
    assert dfp.runs[0]["instruction_details"].get("arguments") == arguments


@pytest.mark.parametrize(
    "raw,executable,arguments",
    [
        ("ENTRYPOINT ['python', 'main.py', '--all']", "python", ['main.py', '--all']),
        ("ENTRYPOINT ['python']", "python", []),
        ("ENTRYPOINT python", "python", []),
    ]
)
def test_entrypoints(raw, executable, arguments):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.entrypoints) == 1
    assert dfp.entrypoints[0]["instruction"] == "ENTRYPOINT"
    assert dfp.entrypoints[0]["instruction_details"].get("executable") == executable
    assert dfp.entrypoints[0]["instruction_details"].get("arguments") == arguments


@pytest.mark.parametrize(
    "raw,executable,arguments",
    [
        ("SHELL ['powershell', '-command']", "powershell", ['-command']),
        ("SHELL powershell", "powershell", [])
    ]
)
def test_shells(raw, executable, arguments):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.shells) == 1
    assert dfp.shells[0]["instruction"] == "SHELL"
    assert dfp.shells[0]["instruction_details"].get("executable") == executable
    assert dfp.shells[0]["instruction_details"].get("arguments") == arguments


@pytest.mark.parametrize(
    "raw,port,protocol",
    [
        ("EXPOSE 8000", "8000", None),
        ("EXPOSE 8001/tdp", "8001", "tdp")
    ]
)
def test_exposes(raw, port, protocol):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.exposes) == 1
    assert dfp.exposes[0]["instruction"] == "EXPOSE"
    assert dfp.exposes[0]["instruction_details"].get("port") == port
    assert dfp.exposes[0]["instruction_details"].get("protocol") == protocol


@pytest.mark.parametrize(
    "raw,workdir",
    [
        ("WORKDIR /app", "/app"),
        ("WORKDIR app", "app"),
        ("WORKDIR /app/src", "/app/src")
    ]
)
def test_workdirs(raw, workdir):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.workdirs) == 1
    assert dfp.workdirs[0]["instruction_details"].get("workdir") == workdir


@pytest.mark.parametrize(
    "raw,stopsignal",
    [
        ("STOPSIGNAL 1337", '1337'),
        ("STOPSIGNAL '1338'", "'1338'"),
        ("STOPSIGNAL whoops", "whoops")
    ]
)
def test_stopsignals(raw, stopsignal):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.stopsignals) == 1
    assert dfp.stopsignals[0]["instruction_details"].get("stopsignal") == stopsignal


@pytest.mark.parametrize(
    "raw,volume",
    [
        ("VOLUME /myvol", "/myvol"),
        ("VOLUME /myvol /secondvol", "/myvol /secondvol"),
        ("VOLUME ['/myvol']", "['/myvol']"),
    ]
)
def test_volumes(raw, volume):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.volumes) == 1
    assert dfp.volumes[0]["instruction_details"].get("volume") == volume


@pytest.mark.parametrize(
    "raw,sub_instruction,executable,arguments",
    [
        ("HEALTHCHECK CMD cat /tmp.txt", "CMD", "cat", "/tmp.txt"),
        ("HEALTHCHECK ['CMD', 'cat', '/tmp.txt']", "CMD", 'cat', ['/tmp.txt'])
    ]
)
def test_healthchecks(raw, sub_instruction, executable, arguments):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.healthchecks) == 1
    assert dfp.healthchecks[0]["instruction_details"].get("sub_instruction") == sub_instruction
    assert dfp.healthchecks[0]["instruction_details"].get("executable") == executable
    assert dfp.healthchecks[0]["instruction_details"].get("arguments") == arguments


@pytest.mark.parametrize(
    "raw,sub_instruction,executable,arguments",
    [
        ("ONBUILD RUN /usr/local/bin/python-build --dir /app/src", "RUN", "/usr/local/bin/python-build",
         "--dir /app/src"),
        ("ONBUILD ['RUN', '/usr/local/bin/python-build', '--dir', '/app/src']", "RUN", '/usr/local/bin/python-build',
         ['--dir', '/app/src'])
    ]
)
def test_onbuilds(raw, sub_instruction, executable, arguments):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.onbuilds) == 1
    assert dfp.onbuilds[0]["instruction_details"].get("sub_instruction") == sub_instruction
    assert dfp.onbuilds[0]["instruction_details"].get("executable") == executable
    assert dfp.onbuilds[0]["instruction_details"].get("arguments") == arguments

