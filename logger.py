import logging
import os
import socket
import sys
from configparser import ConfigParser
from pathlib import Path

from constants import CONFIG_FILE


def get_runnerid():
    config = ConfigParser()
    config.read(CONFIG_FILE)

    tool = config.get('RUNNER_SETTINGS', 'TOOL')

    machine_name = socket.gethostname()

    if "-" in machine_name:
        machine_no = machine_name.strip().split("-", 1)
        machine_no = machine_no[1].strip()
    else:
        machine_no = machine_name.strip()

    runner_id = "K" + tool[:2] + machine_no

    return runner_id


def get_log_path():
    dir = os.path.join(os.getenv("APPDATA"), "Katapult-Runner")
    os_dir = os.path.join(dir, get_runnerid())
    os.makedirs(os_dir, exist_ok=True)
    return os_dir


FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_FILE = Path(get_log_path(), "kat_runner.log")


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler():
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler())
    logger.propagate = False
    log = logging.getLogger('werkzeug')
    log.disabled = True
    return logger
