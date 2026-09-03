"""Named environments for the application under test.

Only non-secret defaults live here. QA_* environment variables (or qa/.env)
override every value, and credentials never belong in this file.
Adapt the entries to the real project after Gate 0 (environment discovery).

The "local" defaults point at the bundled demo application
(assets/demo-app/app.py in the skill) so a fresh scaffold runs green
before it is adapted.
"""

DEFAULT_ENV = "local"

ENVIRONMENTS = {
    "local": {
        "base_url": "http://127.0.0.1:5000",
        "api_base_url": "http://127.0.0.1:5000",
        "api_health_path": "/api/health",
    },
    "staging": {
        "base_url": "",
        "api_base_url": "",
        "api_health_path": "/health",
    },
}
