import requests
import urllib3

from constants import HEADERS, HEALTH_URL
from logger import get_logger

urllib3.disable_warnings()


def check_queue_server_status():
    logger = get_logger('server_status')
    flag = True
    while True:
        try:
            requests.get(HEALTH_URL, verify=False, headers=HEADERS)
            return True
        except Exception as e:
            if flag:
                logger.error("Server Unreachable. Retrying")
                logger.debug(exc_info=True)
                flag = False
