import pytest

from src.analyzer import Analyzer


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
def test_rule_1(raw, errors, warnings):
    dfp = Analyzer(raw_text=raw)
    dfp.rule_1()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors


@pytest.mark.parametrize(
    "arguments,errors,warnings",
    [
        ("ARG api-key", 1, 0),
        ("ARG api-secret=really-secret", 1, 0),
        ("ARG build-id", 0, 0),
        ("ARG owner='me'", 0, 0)
    ]
)
def test_rule_2(arguments, errors, warnings):
    dfp = Analyzer(raw_text=arguments)
    dfp.rule_2()
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
def test_rule_3(users, errors, warnings):
    dfp = Analyzer(raw_text=users)
    dfp.rule_3()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors


@pytest.mark.parametrize(
    "dockerfile,errors,warnings",
    [
        ("Dockerfile", 0, 0),
        ("test.Dockerfile", 0, 0),
        ("Dockerfile.test", 1, 0),
        ("dockerfile", 1, 0),
        ("DockerFile", 1, 0),
    ]
)
def test_rule_4(dockerfile, errors, warnings):
    dfp = Analyzer(raw_text="FROM scratch")
    dfp.dockerfile = dockerfile
    dfp.rule_4()
    result_warnings, result_errors = dfp._return_results()
    assert result_warnings == warnings
    assert result_errors == errors
