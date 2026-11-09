"""Small pytest plugin copied into each temporary evaluation directory.

Exit code 1 alone is ambiguous: broken fixtures can produce it too. These
hooks separate behavioral failures from errors in the test infrastructure.
"""

import json
from pathlib import Path

import pytest


counts = dict(passed=0, failed=0, errors=0, skipped=0, collected=0)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.skipped:
        counts["skipped"] += 1
    elif report.failed:
        # Assertions and pytest.fail/raises failures express test expectations.
        # Exceptions raised in solution.py also show mutant behavior (e.g. the
        # existing mutant which raises ValueError for a zero order total).
        behavioral = call.excinfo is not None and (
            isinstance(call.excinfo.value, (AssertionError, pytest.fail.Exception))
            or any(Path(entry.path) == item.config.rootpath / "solution.py"
                   for entry in call.excinfo.traceback)
        )
        key = "failed" if report.when == "call" and behavioral else "errors"
        counts[key] += 1
    elif report.when == "call" and report.passed:
        counts["passed"] += 1


def pytest_collectreport(report):
    if report.failed:
        counts["errors"] += 1


def pytest_sessionfinish(session, exitstatus):
    counts["collected"] = session.testscollected
    (session.config.rootpath / "pytest_results.json").write_text(
        json.dumps(counts), encoding="utf-8",
    )
