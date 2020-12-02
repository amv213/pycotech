import logging
import pycotech.loggers
import pycotech.utils

logger = logging.getLogger(__name__)
logger.setLevel("WARNING")  # (default) best practice

# Uncomment if want to prevent ALL library’s logged events being output to
# sys.stderr in the absence of user-side logging configuration
# logger.addHandler(logging.NullHandler())

