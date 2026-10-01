"""Expected failures are values; uncertain physical outcomes terminate an episode."""
class PRLError(Exception):
    pass

class ValidationError(PRLError):
    pass

class Unavailable(PRLError):
    pass

class BudgetExceeded(PRLError):
    pass

class UncertainExecution(PRLError):
    """A write may have happened. Never retry it automatically."""

class Interrupted(PRLError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason

class NativeTerminal(Interrupted):
    def __init__(self, success: bool):
        super().__init__("native_success" if success else "native_truncated")
        self.success = success
