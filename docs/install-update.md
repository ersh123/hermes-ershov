# Install and update Hermes Mnemos

Hermes Mnemos ships as a Hermes plugin. Install it through Hermes, then use the `hermes mnemos ...` commands inside your Hermes session.

## Install from GitHub

```bash
hermes plugins install ersh123/hermes-mnemos --enable
```

## Install from a local checkout

```bash
hermes plugins install file:///path/to/hermes-mnemos --enable
```

## Confirm the plugin is available

```bash
hermes mnemos review --help
```

If you are outside Hermes, the repo still exposes the same CLI as the `mnemos` console script, and `python -m hermes_mnemos` works as a fallback during local development.

## Install nightly memory outside the gateway

For VPS deployments, prefer a user systemd timer when you want the nightly memory
loop to survive Hermes gateway restarts or crashes:

```bash
mnemos install-systemd --on-calendar "*-*-* 03:00:00"
```

The timer runs `mnemos nightly` through a generated no-agent script. It stages
artifacts, writes digests, compacts terminal artifacts, and updates the run
ledger. It does not apply live memory automatically and does not restart Hermes.
Provider secrets are not written by the installer. If the timer needs DeepSeek,
put the key in `~/.config/hermes-mnemos/nightly.secrets.env`; the generated
service reads that file if it exists and leaves it untouched on reinstall.

## Update the installed checkout

```bash
hermes mnemos update
hermes mnemos update --check
hermes mnemos update --no-verify
```

The update command is conservative on purpose:

- default remote: `origin`
- default branch: `main`
- it refuses a dirty working tree
- it refuses local-ahead or diverged history
- it runs pytest after a real update unless you disable verification

You can override the remote or branch if your install tracks something else:

```bash
hermes mnemos update --remote upstream --branch release
```

## When to use the update check

Use `hermes mnemos update --check` before a real pull if you just want to see whether the install is behind.
Use the real update when you are ready to fast-forward the checkout and run verification.

For the offline walkthrough, jump to `docs/quickstart.md`.
