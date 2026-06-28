# Release integrity

Release candidates are valid only when:

- product coverage is 100%;
- CI is green;
- CodeQL is green;
- wheel and source distribution build cleanly;
- Twine metadata check passes;
- README describes the same public CLI that `pyproject.toml` exports.
