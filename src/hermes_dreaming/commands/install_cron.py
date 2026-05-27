from __future__ import annotations

JOB_NAME = "hermes-dreaming"
DEFAULT_SCHEDULE = "0 3 * * *"
_PROMPT = "/dreaming review"


def _find_existing(list_jobs_fn) -> dict | None:
    try:
        for job in list_jobs_fn(include_disabled=True):
            if job.get("name") == JOB_NAME:
                return job
    except Exception:
        return None
    return None


def handle(schedule: str | None = None) -> str:
    """Register a nightly review-only Hermes cron job when available."""

    try:
        from cron.jobs import create_job, list_jobs
    except ImportError:
        return (
            "## hermes dreaming install-cron\n\n"
            "**Error:** Hermes cron module not available in this environment.\n\n"
            "Start Hermes in an environment that exposes `cron.jobs`, then retry."
        )

    schedule = (schedule or DEFAULT_SCHEDULE).strip()

    existing = _find_existing(list_jobs)
    if existing:
        return (
            "## hermes dreaming install-cron\n\n"
            f"**Already installed.** A cron job named `{JOB_NAME}` exists:\n\n"
            f"- Job ID:   `{existing['id']}`\n"
            f"- Schedule: {existing.get('schedule_display', existing.get('schedule', '?'))}\n"
            f"- Enabled:  {existing.get('enabled', True)}\n"
            f"- Next run: {existing.get('next_run_at', 'unknown')}\n\n"
            "This job runs the review-only dreaming flow, so it stays safe and observable."
        )

    try:
        job = create_job(
            prompt=_PROMPT,
            schedule=schedule,
            name=JOB_NAME,
            deliver="local",
        )
    except Exception as exc:
        return (
            "## hermes dreaming install-cron\n\n"
            f"**Error creating cron job:** {exc}\n\n"
            f"Check that the schedule expression `{schedule}` is valid "
            "(for example, `0 3 * * *` for nightly at 03:00)."
        )

    job_id = job["id"]
    schedule_display = job.get("schedule_display", schedule)
    next_run = job.get("next_run_at", "unknown")

    return (
        "## hermes dreaming install-cron\n\n"
        f"**Cron job registered.**\n\n"
        f"- Job ID:    `{job_id}`\n"
        f"- Name:      `{JOB_NAME}`\n"
        f"- Schedule:  {schedule_display}\n"
        f"- Next run:  {next_run}\n"
        f"- Delivers:  local review output\n\n"
        "Each night Hermes will run `/dreaming review` in a fresh session, "
        "so the loop stays dry-run only until the apply path is explicitly used."
    )
