"""EXAMPLE session hooks: run once per run (once per worker in --parallel).

Use setup_session for one-time seeding through the API and teardown_session
to undo it. Tests read what you store here through ctx.session.store.
"""

from __future__ import annotations


def setup_session(session):
    """Record what the backend reports about itself; skip silently when there is no API."""
    if not session.settings.api_base_url:
        return
    try:
        response = session.api.get(session.settings.api_health_path)
        session.store["health"] = (
            response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text[:200]
        )
        session.log.info("session: health=%s", session.store["health"])
    except Exception as error:  # noqa: BLE001 - ENV-003 reports this properly; do not fail the whole run here
        session.log.warning("session: health check unavailable: %r", error)


def teardown_session(session):
    session.log.info("session: done")
