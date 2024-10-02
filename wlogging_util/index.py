import atexit
import logging
import logging.config
import logging.handlers
import os

# Log file sizes in MB and number of backups for each log file
LOG_FILESIZE_TO_KEEP = 5
LOG_BACKUP_COUNT = 10

# Root directory of the project
# If it's installed as a package, in a venv
# the we need to go up three directories (packages are in: .venv/Lib/site-packages).
# If it's imported from somewhere else, we set the ROOT_DIR to None and require the
# user to provide the root directory of the project as an argument when creating the
# WloggingUtil object.
if ".venv" in os.path.dirname(os.path.abspath(__file__)):
    ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../")
else:
    ROOT_DIR = None

# If logs directory doesn't exist, create it
LOGS_DIR = None
LOGFILE_FILEPATH = None


LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {
            "format": "{message}",
            "style": "{",
        },
        "simple": {
            "format": "{asctime:<23s} - {levelname:^7s} - {module} - {message}",
            "style": "{",
        },
        "json": {
            "()": "wlogging_util.formatters.JSONFormatter",
            "fmt_keys": {
                "level": "levelname",
                "timestamp": "timestamp",
                "message": "message",
                "logger": "name",
                "pathname": "pathname",
                "module": "module",
                "function": "funcName",
                "line": "lineno",
                "thread_name": "threadName",
            },
        },
    },
    "filters": {
        "non_module": {"()": "wlogging_util.index.WloggingUtil.FilterNonRootLoggers"},
        "non_out": {"()": "wlogging_util.filters.FilterOutOUT"},
        "out_only": {"()": "wlogging_util.filters.FilterOutNonOUT"},
        "ipykernel": {"()": "wlogging_util.filters.AllowIpykernel"},
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
            "filters": ["non_module", "non_out", "ipykernel"],
        },
        "stdout_out": {
            "class": "logging.StreamHandler",
            "level": "OUT",
            "formatter": "plain",
            "stream": "ext://sys.stdout",
            "filters": ["non_module", "out_only"],
        },
        "logfile": {
            "class": "concurrent_log_handler.ConcurrentRotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": LOGFILE_FILEPATH,
            "filters": ["non_module", "non_out", "ipykernel"],
            "maxBytes": LOG_FILESIZE_TO_KEEP * 1000000,
            "backupCount": LOG_BACKUP_COUNT,
            "encoding": "utf-8",
        },
        "queue_handler": {
            "class": "logging.handlers.QueueHandler",
            "handlers": [
                "logfile",
            ],
            "respect_handler_level": True,
        },
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["queue_handler", "stdout"],
        }
    },
}


def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError("{} already defined in logging module".format(levelName))
    if hasattr(logging, methodName):
        raise AttributeError("{} already defined in logging module".format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError("{} already defined in logger class".format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


class WloggingUtil:
    def __init__(
        self,
        root_dir: str = None,
        level: str = "WARNING",
        logfile_size: int = None,
        log_backup_count: int = None,
    ):
        if not ROOT_DIR and not root_dir:  # noqa: F823
            raise ValueError(
                "Root directory of the project must be provided as an argument."
            )

        if root_dir:
            ROOT_DIR = root_dir

        if logfile_size:
            LOG_FILESIZE_TO_KEEP = logfile_size  # noqa: F841

        if log_backup_count:
            LOG_BACKUP_COUNT = log_backup_count  # noqa: F841

        LOGS_DIR = os.path.join(ROOT_DIR, "./logs")
        LOGFILE_FILEPATH = os.path.join(LOGS_DIR, "logs.log")  # noqa: F841
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)

        self.logger = None
        self._level = level
        LOGGER_CONFIG["handlers"]["stdout"]["level"] = level

        # We create a new logging level that's like a print statement
        # We set it higher than CRITICAL so that it always gets printed
        try:
            # We add the new logging level
            addLoggingLevel("OUT", 100)
        except AttributeError:
            pass

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level: str):
        if level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(
                "Invalid log level. Must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL."
            )
        self._level = level
        # We check if the stdout handler exists and adjust its level
        if self.logger and "stdout" in list(logging.getHandlerNames()):
            logging.getHandlerByName("stdout").setLevel(level)
            logging.getHandlerByName("stdout_file").setLevel(level)
        else:
            LOGGER_CONFIG["handlers"]["stdout"]["level"] = level
            LOGGER_CONFIG["handlers"]["stdout_file"]["level"] = level

    @property
    def get_handlers(self):
        return list(logging.getHandlerNames())

    def add_filter(self, filter_name: str, filter_class_path: dict):
        LOGGER_CONFIG["filters"][filter_name] = {"()": filter_class_path}

    def remove_filter(self, filter_name: str):
        del LOGGER_CONFIG["filters"][filter_name]

    def get_logger(self, level: str = None):
        if level:
            self.level = level

        # Configure the logger
        logging.config.dictConfig(LOGGER_CONFIG)

        # Set it up so that the queue handler is started and stopped when the program starts and stops
        queue_handler = logging.getHandlerByName("queue_handler")
        if queue_handler is not None:
            queue_handler.listener.start()
            atexit.register(queue_handler.listener.stop)

        # Setup the logger if it's not already set up
        if not self.logger:
            self.logger = logging.getLogger("wlogging_logger")

        # Return the logger
        return self.logger

    class FilterNonRootLoggers(logging.Filter):
        """Filter out loggers that are not from root."""

        def __init__(self, name="wlogging_logger"):
            super().__init__(name)

        def filter(self, record):
            # Filter out loggers that are not from the root directory
            record.pathname = record.pathname.lower()
            return ROOT_DIR in record.pathname and ".venv" not in record.pathname
