import logging
import os
from datetime import datetime

# Define log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Cache for loggers to avoid duplicate handlers
_loggers = {}

def get_endpoint_logger(endpoint_name: str) -> logging.Logger:
    """
    Get a logger specific to an API endpoint that writes to its own file.
    """
    if endpoint_name in _loggers:
        return _loggers[endpoint_name]
    
    logger = logging.getLogger(endpoint_name)
    logger.setLevel(logging.DEBUG)
    
    # Create file handler
    log_file = os.path.join(LOG_DIR, f"{endpoint_name}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | [%(levelname)s] | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    _loggers[endpoint_name] = logger
    
    return logger
