import pytest

from src.dokter.analyzer import Analyzer


@pytest.mark.parametrize(
    "rule,out",
    [
        ("not_a_rule", "Rule does not exists")
    ]
)
def test_explain(rule, out):
    dfp = Analyzer(raw_text="")
    assert dfp.explain(rule=rule) == out


@pytest.mark.parametrize(
    "raw,severity,count",
    [
        ("COPY secrets.py . ", "critical", 1),
        ("COPY just_a_file.txt secrets.txt", "critical", 1),
        ("COPY . secrets.txt", "critical", 1),
        ("COPY local.env .env", "critical", 1),
        ("COPY . /app", "critical", 0),
        ("COPY . .", "critical", 0),
        ("COPY app/ .", "critical", 0),
    ]
)
def test_dfa001(raw, severity, count):
    dfp = Analyzer(raw_text=raw)
    dfp.dfa001()
    result = dfp._return_results()
    assert result.get(severity.upper(), 0) == count


@pytest.mark.parametrize(
    "dockerignore,severity,count",
    [
        ("../.dockerignore", "info", 0),
        ("", "info", 1)
    ]
)
def test_dfa002(dockerignore, severity, count):
    dfp = Analyzer(raw_text="FROM python:3.10.0", dockerignore=dockerignore)
    dfp.dfa002()
    result = dfp._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "raw,severity,count",
    [
        ("COPY secrets.py . ", "major", 0),
        ("COPY . secrets.txt", "major", 1),
        ("COPY . /app", "major", 1),
        ("COPY . .", "major", 1),
        ("COPY app/ .", "major", 0),
    ]
)
def test_dfa003(raw, severity, count):
    dfp = Analyzer(raw_text=raw)
    dfp.dfa003()
    result = dfp._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "arguments,severity,count",
    [
        ("ARG api-key", "critical", 1),
        ("ARG API-KEY", "critical", 1),
        ("ARG api-secret=really-secret", "critical", 1),
        ("ARG build-id", "critical", 0),
        ("ARG owner='me'", "critical", 0)
    ]
)
def test_dfa004(arguments, severity, count):
    dfp = Analyzer(raw_text=arguments)
    dfp.dfa004()
    result = dfp._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "users,severity,count",
    [
        ("USER ADMIN", "major", 0),
        ("USER root", "major", 1),
        ("USER root:1000", "major", 1),
        ("USER root \nUSER nobody", "major", 0)
    ]
)
def test_dfa005(users, severity, count):
    dfp = Analyzer(raw_text=users)
    dfp.dfa005()
    result = dfp._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "dockerfile,severity,count",
    [
        ("Dockerfile", "minor", 0),
        ("test.Dockerfile", "minor", 0),
        ("Dockerfile.test", "minor", 1),
        ("dockerfile", "minor", 1),
        ("DockerFile", "minor", 1),
    ]
)
def test_dfa006(dockerfile, severity, count):
    dfp = Analyzer(raw_text="FROM scratch")
    dfp.dockerfile = dockerfile
    dfp.dfa006()
    result = dfp._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "raw,severity,count",
    [
        ("ADD main.py . ", "minor", 1),
        ("ADD --chown=me:me . /app", "minor", 1),
        ("ADD main.tar.gz . ", "minor", 0),
        ("ADD main.gz . ", "minor", 0),
        ("ADD --chown=me:me app.tar.gz /app", "minor", 0),
        ("ADD http://ipv4.download.thinkbroadband.com/5MB.zip /small_file.mp3", "minor", 0),
        ("ADD --chown=me:me http://ipv4.download.thinkbroadband.com/5MB.zip /small_file.mp3", "minor", 0),
    ]
)
def test_dfa007(raw, severity, count):
    dfp = Analyzer(raw_text=raw)
    dfp.dfa007()
    result = dfp._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "users,severity,count",
    [
        ("RUN apt-get update \nRUN apt-get upgrade", "major", 2),
        ("USER apt-get update && apt-get upgrade", "major", 0),
    ]
)
def test_dfa008(users, severity, count):
    dfp = Analyzer(raw_text=users)
    dfp.dfa008()
    result = dfp._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


def test_dfa009():
    pass


@pytest.mark.parametrize(
    "users,severity,count",
    [
        ('HEALTHCHECK CMD cat /tmp.txt \nCMD ["python", "main.py", "--only-data"]', "info", 0),
        ('CMD ["python", "main.py", "--only-data"]', "info", 1),
    ]
)
def test_dfa010(users, severity, count):
    dfp = Analyzer(raw_text=users)
    dfp.dfa010()
    result = dfp._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "raw,severity,count",
    [
        ("RUN echo $USER", "minor", 1),
        ("RUN [[ n != 0 ]]", "major", 1)
    ]
)
def test_dfa_shellcheck(raw, severity, count):
    dfp = Analyzer(raw_text=raw)
    dfp.dfa000_shellcheck()
    result = dfp._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count
