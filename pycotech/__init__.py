import logging
import pycotech.loggers

logger = logging.getLogger(__name__)
logger.setLevel("WARNING")  # best practice

# Uncomment if want to prevent ALL library’s logged events being output to
# sys.stderr in the absence of user-side logging configuration
# logger.addHandler(logging.NullHandler())

