import pytest

from src.dokter.analyzer import Analyzer


@pytest.mark.parametrize(
    "rule,out",
    [
        ("not_a_rule", "Rule does not exists")
    ]
)
def test_explain(rule, out):
    dfa = Analyzer(raw_text="")
    assert dfa.explain(rule=rule) == out


@pytest.mark.parametrize(
    "raw,severity,count",
    [
        ("RUN echo $USER", "minor", 1),
        ("RUN [[ n != 0 ]]", "major", 1)
    ]
)
def test_dfa000(raw, severity, count):
    dfa = Analyzer(raw_text=raw)
    dfa.dfa000_shellcheck()
    result = dfa._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


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
    dfa = Analyzer(raw_text=raw)
    dfa.dfa001()
    result = dfa._return_results()
    assert result.get(severity.upper(), 0) == count


@pytest.mark.parametrize(
    "dockerignore,severity,count",
    [
        ("../.dockerignore", "info", 0),
        ("", "info", 1)
    ]
)
def test_dfa002(dockerignore, severity, count):
    dfa = Analyzer(raw_text="FROM python:3.10.0", dockerignore=dockerignore)
    dfa.dfa002()
    result = dfa._return_results()
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
    dfa = Analyzer(raw_text=raw)
    dfa.dfa003()
    result = dfa._return_results()
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
    dfa = Analyzer(raw_text=arguments)
    dfa.dfa004()
    result = dfa._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "users,severity,count,formatted",
    [
        ("USER ADMIN", "major", 0, "USER ADMIN\n"),
        ("USER root", "major", 1, "WORKDIR /app\nRUN useradd -M appuser && chown -R appuser /app\nUSER appuser\n"),
        ("USER root:1000", "major", 1, "WORKDIR /app\nRUN useradd -M appuser && chown -R appuser /app\nUSER appuser\n"),
        ("USER root \nUSER nobody", "major", 0, "USER nobody\n")
    ]
)
def test_dfa005(users, severity, count, formatted):
    dfa = Analyzer(raw_text=users)
    dfa.dfa005()
    result = dfa._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count
    assert dfa.dfp.users[-1]["formatted"] == formatted


@pytest.mark.parametrize(
    "dockerfile,severity,count",
    [
        ("Dockerfile", "minor", 0),
        ("test.Dockerfile", "minor", 0),
        ("Dockerfile.test", "minor", 1),
        ("dockerfile", "minor", 1),
        ("DockerFile", "minor", 1),
        ("src/Dockerfile", "minor", 0),
        ("src/api/api.Dockerfile", "minor", 0),
        ("src/api/api-Dockerfile", "minor", 1)
    ]
)
def test_dfa006(dockerfile, severity, count):
    dfa = Analyzer(raw_text="FROM scratch")
    dfa.dockerfile = dockerfile
    dfa.dfa006()
    result = dfa._return_results()
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
    dfa = Analyzer(raw_text=raw)
    dfa.dfa007()
    result = dfa._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "raw,severity,count",
    [
        ("RUN apt-get update \nRUN apt-get upgrade", "major", 2),
        ("USER apt-get update && apt-get upgrade", "major", 0),
    ]
)
def test_dfa008(raw, severity, count):
    dfa = Analyzer(raw_text=raw)
    dfa.dfa008()
    result = dfa._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


def test_dfa009():
    pass


@pytest.mark.parametrize(
    "raw,severity,count",
    [
        ('HEALTHCHECK CMD cat /tmp.txt \nCMD ["python", "main.py", "--only-data"]', "info", 0),
        ('CMD ["python", "main.py", "--only-data"]', "info", 1),
    ]
)
def test_dfa010(raw, severity, count):
    dfa = Analyzer(raw_text=raw)
    dfa.dfa010()
    result = dfa._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "raw,severity,count",
    [
        ('CMD ["python", "main.py", "--only-data"]\nRUN apt-get update', "major", 1),
        ('CMD ["python", "main.py", "--only-data"]', "major", 0),
    ]
)
def test_dfa011(raw, severity, count):
    dfa = Analyzer(raw_text=raw)
    dfa.dfa011()
    result = dfa._return_results()
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


@pytest.mark.parametrize(
    "maintainer,severity,count,formatted",
    [
        ("MAINTAINER Fred", "major", 1, "LABEL maintainer=Fred\n"),
        ("MAINTAINER 'Fred'", "major", 1, "LABEL maintainer='Fred'\n"),
    ]
)
def test_dfa012(maintainer,  severity, count, formatted):
    dfa = Analyzer(raw_text=maintainer)
    dfa.dfa012()
    result = dfa._return_results()
    assert dfa.dfp.maintainers[0]["formatted"] == formatted
    assert result.get(severity.upper(), 0) == count
    assert sum(result.values()) == count


