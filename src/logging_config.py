# src/logging_config.py
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = "app.log"

def setup_logging(log_level=logging.INFO):
    """
    Configures basic file logging for the application.
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_file_path = os.path.join(LOG_DIR, LOG_FILE)

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Prevent adding multiple handlers if called more than once (e.g. in tests or reloads)
    if any(isinstance(h, RotatingFileHandler) and h.baseFilename == os.path.abspath(log_file_path) for h in logger.handlers):
        return

    # Create a rotating file handler
    # Rotates when log file reaches 5MB, keeps up to 5 backup logs.
    file_handler = RotatingFileHandler(
        log_file_path, 
        maxBytes=5*1024*1024, # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(formatter)

    # Add the handler to the root logger
    logger.addHandler(file_handler)

    # Optional: Add a StreamHandler to also log to console (useful for development/debugging)
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.DEBUG) # Or another level
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)

    print(f"Logging configured. Log level: {logging.getLevelName(logger.getEffectiveLevel())}. Log file: {log_file_path}")

if __name__ == '__main__':
    # Example usage:
    setup_logging(log_level=logging.DEBUG)
    logging.debug("This is a debug message.")
    logging.info("This is an info message.")
    logging.warning("This is a warning message.")
    logging.error("This is an error message.")
    logging.critical("This is a critical message.")

    # Example from another module
    logger_example = logging.getLogger("my_module_example")
    logger_example.info("Info message from my_module_example")
