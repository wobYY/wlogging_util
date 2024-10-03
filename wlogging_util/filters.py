import logging


class FilterOutOUT(logging.Filter):
    """Filter out logging messages that are OUT."""

    def __init__(self, name="wlogging_logger"):
        super().__init__(name)

    def filter(self, record):
        # Filter out OUT level
        return str(record.levelname).lower() != "out"


class FilterOutNonOUT(logging.Filter):
    """Filter out logging messages that are not OUT."""

    def __init__(self, name="wlogging_logger"):
        super().__init__(name)

    def filter(self, record):
        # Filter out non OUT levels
        return str(record.levelname).lower() == "out"


class AllowIpykernel(logging.Filter):
    """Filter out logging messages that are not OUT."""

    def __init__(self, name="wlogging_logger"):
        super().__init__(name)

    def filter(self, record):
        # Allow ipykernel logs
        return "ipykernel" in str(record.pathname).lower()
