"""Named environments for the application under test.

Only non-secret defaults live here. QA_* environment variables (or qa/.env)
override every value, and credentials never belong in this file.
Adapt the entries to the real project after Gate 0 (environment discovery).
"""

DEFAULT_ENV = "local"

ENVIRONMENTS = {
    "local": {
        "base_url": "http://localhost:3000",
        "api_base_url": "http://localhost:8000",
        "api_health_path": "/health",
    },
    "staging": {
        "base_url": "",
        "api_base_url": "",
        "api_health_path": "/health",
    },
}
