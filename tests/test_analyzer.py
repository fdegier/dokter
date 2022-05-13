import pytest

from src.analyzer import Analyzer


@pytest.mark.parametrize(
    "raw,errors,warning",
    [
        ("COPY secrets.py . ", 1, 0),
        # ("COPY local.env .env", 1, 0),
        # ("COPY . /app", 0, 0),
    ]
)
def test_rule_1(raw, errors, warning):
    dfp = Analyzer(raw_text=raw)
    result_warnings, result_errors = dfp.run()
    assert result_warnings == warning
    assert result_errors == errors
