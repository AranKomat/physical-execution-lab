class ContractError(ValueError):
    """A request violates the declared execution or evidence contract."""

class Unavailable(RuntimeError):
    """An explicitly requested backend is not available. Never silently fall back."""

class StopExecution(RuntimeError):
    """Controlled stop after a native action; do not retry that action."""
    def __init__(self, reason):
        self.reason = str(reason)
        super().__init__(self.reason)

class TransportUncertain(RuntimeError):
    """A dispatched request has no authoritative response. Do not auto-retry."""
