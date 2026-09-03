"""Static reference data shared by tests. Adapt to the application under test.

Keep this to stable facts (roles, known messages, enum values). Anything that
must be unique per test belongs in factories.py.
"""

ROLES = ("admin", "user")

# Fill after Gate 1 from the real implementation, not from documentation.
KNOWN_MESSAGES = {
    "invalid_credentials": "",
    "required_field": "",
}
