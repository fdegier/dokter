import pytest

from src.dockter.analyzer import Analyzer


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
    "raw,errors,warnings",
    [
        ("COPY secrets.py . ", 1, 0),
        ("COPY just_a_file.txt secrets.txt", 1, 0),
        ("COPY . secrets.txt", 1, 0),
        ("COPY local.env .env", 1, 0),
        ("COPY . /app", 0, 0),
        ("COPY . .", 0, 0),
        ("COPY app/ .", 0, 0),
    ]
)
def test_dfa001(raw, errors, warnings):
    dfp = Analyzer(raw_text=raw)
    dfp.dfa001()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors


@pytest.mark.parametrize(
    "dockerignore,errors,warnings",
    [
        ("../.dockerignore", 0, 0),
        ("", 0, 1)
    ]
)
def test_dfa002(dockerignore, errors, warnings):
    dfp = Analyzer(raw_text="FROM python:3.10.0", dockerignore=dockerignore)
    dfp.dfa002()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors


@pytest.mark.parametrize(
    "raw,errors,warnings",
    [
        ("COPY secrets.py . ", 0, 0),
        ("COPY . secrets.txt", 1, 0),
        ("COPY . /app", 1, 0),
        ("COPY . .", 1, 0),
        ("COPY app/ .", 0, 0),
    ]
)
def test_dfa003(raw, errors, warnings):
    dfp = Analyzer(raw_text=raw)
    dfp.dfa003()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors


@pytest.mark.parametrize(
    "arguments,errors,warnings",
    [
        ("ARG api-key", 1, 0),
        ("ARG API-KEY", 1, 0),
        ("ARG api-secret=really-secret", 1, 0),
        ("ARG build-id", 0, 0),
        ("ARG owner='me'", 0, 0)
    ]
)
def test_dfa004(arguments, errors, warnings):
    dfp = Analyzer(raw_text=arguments)
    dfp.dfa004()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors


@pytest.mark.parametrize(
    "users,errors,warnings",
    [
        ("USER ADMIN", 0, 0),
        ("USER root", 1, 0),
        ("USER root:1000", 1, 0),
        ("USER root \nUSER nobody", 0, 0)
    ]
)
def test_dfa005(users, errors, warnings):
    dfp = Analyzer(raw_text=users)
    dfp.dfa005()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors


@pytest.mark.parametrize(
    "dockerfile,errors,warnings",
    [
        ("Dockerfile", 0, 0),
        ("test.Dockerfile", 0, 0),
        ("Dockerfile.test", 0, 1),
        ("dockerfile", 0, 1),
        ("DockerFile", 0, 1),
    ]
)
def test_dfa006(dockerfile, errors, warnings):
    dfp = Analyzer(raw_text="FROM scratch")
    dfp.dockerfile = dockerfile
    dfp.dfa006()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors


@pytest.mark.parametrize(
    "raw,errors,warnings",
    [
        ("ADD main.py . ", 0, 1),
        ("ADD --chown=me:me . /app", 0, 1),
        ("ADD main.tar.gz . ", 0, 0),
        ("ADD main.gz . ", 0, 0),
        ("ADD --chown=me:me app.tar.gz /app", 0, 0),
        ("ADD http://ipv4.download.thinkbroadband.com/5MB.zip /small_file.mp3", 0, 0),
        ("ADD --chown=me:me http://ipv4.download.thinkbroadband.com/5MB.zip /small_file.mp3", 0, 0),
    ]
)
def test_dfa007(raw, errors, warnings):
    dfp = Analyzer(raw_text=raw)
    dfp.dfa007()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors


@pytest.mark.parametrize(
    "users,errors,warnings",
    [
        ("RUN apt-get update \nRUN apt-get upgrade", 2, 0),
        ("USER apt-get update && apt-get upgrade", 0, 0),
    ]
)
def test_dfa008(users, errors, warnings):
    dfp = Analyzer(raw_text=users)
    dfp.dfa008()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors


def test_dfa009():
    pass


@pytest.mark.parametrize(
    "users,errors,warnings",
    [
        ('HEALTHCHECK CMD cat /tmp.txt \nCMD ["python", "main.py", "--only-data"]', 0, 0),
        ('CMD ["python", "main.py", "--only-data"]', 0, 1),
    ]
)
def test_dfa010(users, errors, warnings):
    dfp = Analyzer(raw_text=users)
    dfp.dfa010()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors

