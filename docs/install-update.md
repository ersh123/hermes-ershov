# Install and update Hermes Dreaming

Hermes Dreaming ships as a Hermes plugin. Install it through Hermes, then use the `hermes dreaming ...` commands inside your Hermes session.

## Install from GitHub

```bash
hermes plugins install asimons81/hermes-dreaming --enable
```

## Install from a local checkout

```bash
hermes plugins install file:///path/to/hermes-dreaming --enable
```

## Confirm the plugin is available

```bash
hermes dreaming review --help
```

If you are outside Hermes, the repo still exposes the same CLI as the `dreaming` console script, and `python -m hermes_dreaming` works as a fallback during local development.

## Update the installed checkout

```bash
hermes dreaming update
hermes dreaming update --check
hermes dreaming update --no-verify
```

The update command is conservative on purpose:

- default remote: `origin`
- default branch: `main`
- it refuses a dirty working tree
- it refuses local-ahead or diverged history
- it runs pytest after a real update unless you disable verification

You can override the remote or branch if your install tracks something else:

```bash
hermes dreaming update --remote upstream --branch release
```

## When to use the update check

Use `hermes dreaming update --check` before a real pull if you just want to see whether the install is behind.
Use the real update when you are ready to fast-forward the checkout and run verification.

For the offline walkthrough, jump to `docs/quickstart.md`.
