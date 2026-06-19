from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_shows_release_shaped_test_matrix() -> None:
    text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    for version in ("'3.11'", "'3.12'", "'3.13'"):
        assert version in text
    for gate in (
        "git diff --check",
        "python -m compileall -q __init__.py src scripts",
        "pytest -q",
        "--cov=hermes_dreaming",
        "--cov-report=xml",
        "--cov-fail-under=80",
        "pytest -q tests/test_pbt.py",
        "python scripts/hermes_plugin_smoke.py",
        "python -m build",
        "dist/*.whl",
        "dist/*.tar.gz",
        "/tmp/ershov-wheel-smoke/bin/ershov --help",
        "/tmp/ershov-sdist-smoke/bin/ershov --help",
        "providers doctor --provider offline-marker --strict",
        "providers doctor --provider deepseek --env-file /tmp/ershov-wheel-nightly.env --fix-plan --strict",
        "status --release-gate",
        "status --release-gate --state-root /tmp/ershov-wheel-smoke-state --require-provider deepseek --provider-env-file /tmp/ershov-wheel-nightly.env --fix-plan",
        "soak --state-root /tmp/ershov-wheel-smoke-state --since-hours 30 --min-successful 1 --require-timer --require-source systemd",
        "DEEPSEEK_API_KEY=<secret>",
        "sk-ci-do-not-print",
        "secret leaked from soak fix-plan",
    ):
        assert gate in text


def test_codeql_workflow_is_scheduled_and_pr_gated() -> None:
    text = (REPO_ROOT / ".github" / "workflows" / "codeql.yml").read_text(encoding="utf-8")

    assert "pull_request:" in text
    assert "schedule:" in text
    assert "workflow_dispatch:" in text
    assert "languages: python" in text


def test_python_classifier_matches_ci_matrix() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    testing_doc = (REPO_ROOT / "docs" / "testing.md").read_text(encoding="utf-8")

    for version in ("3.11", "3.12", "3.13"):
        assert f"'{version}'" in ci
        assert f"Programming Language :: Python :: {version}" in pyproject
        assert version in testing_doc
