"""Public policy only. Actual key values come from the local environment."""

CALLER_ENV = {
    "dispatch": "FIELDCARE_DISPATCH_KEY",
    "partner": "FIELDCARE_PARTNER_KEY",
}
# Begin with authentication alone. Set the policy during the rate-limit task.
POLICY = None
