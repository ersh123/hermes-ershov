# Testing

`self-ershov-memory` is product-only. The public package ships only `self_ershov_memory` and the `self-ershov-memory` CLI.

## Required gate

```bash
uv run --locked --extra dev pytest --cov=src/self_ershov_memory --cov=__init__ --cov-report=term-missing --cov-fail-under=100 -q
uv run --locked --extra dev ruff check --select F401,F841,E731 __init__.py src tests
uv run --locked --extra dev python -m build
uv run --locked --extra dev twine check --strict dist/*.whl dist/*.tar.gz
```

The coverage gate is intentionally 100% for the product package. Legacy staged-memory code is removed instead of carried as compatibility surface.
