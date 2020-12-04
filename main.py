import json
import random
import time
from threading import Thread, Lock

import requests
from flask import Flask

from check_server_status import check_queue_server_status
from clean_data import delete_file
from constants import HEADERS, URL
from logger import get_logger
from utils import process_data, runner_details


def get_project(index, runner_id, tool, executable_command, time_betw_jobs):
    logger = get_logger('executor-' + str(index))
    logger.info("Executor Thread Started")
    flag = True
    while True:
        try:
            delete_file()
            r = requests.get(URL + "toolqueue/projects/getnext?" +
                             "runnerId=" + runner_id + "-" + str(index) + "&toolName=" + tool, headers=HEADERS)
            if r.status_code == 200:
                extract_data = r.json()
                try:
                    process_data(extract_data, index, runner_id, executable_command, time_betw_jobs)
                except Exception as e:
                    logger.debug(e, exc_info=True)
            elif r.status_code == 400:
                data = json.loads(r.content.decode("utf-8"))
                if data['message'] == "No Projects In Queue":
                    if flag:
                        logger.info("Waiting For Project")
                        flag = False

                elif data['message'] == "Runner Disabled":
                    if flag:
                        logger.info("Runner Disabled")
                        flag = False
            time.sleep(10)
        except:
            continue


def get_avail_project(count, runner_id, tool, executable_command, time_betw_jobs):
    lock = Lock()
    threads = []

    num_acquires = 0
    while num_acquires < int(count):
        acquired = lock.acquire(0)

        for index in range(int(count)):
            t = Thread(target=get_project, args=(str(index + 1), runner_id, tool, executable_command, time_betw_jobs))
            if acquired:
                num_acquires += 1

            t.start()
            time.sleep(2)
            threads.append(t)

        for t in threads:
            t.join()
            lock.release()


def post_status(runner_id, tool, machine_name, concurrent_count, log_port):
    logger = get_logger('server_coordination')
    connect_flag = True
    flag = True
    while True:
        try:
            runner_data = {
                'runnerId': runner_id,
                'machineName': machine_name,
                'toolName': tool,
                'concurrent': concurrent_count,
                'port': log_port
            }
            r = requests.post(URL + 'toolqueue/runners/add/', json=runner_data, headers=HEADERS)
            if r.status_code == 200:
                if flag:
                    logger.info("Runner Info Sent To Server")
                    flag = False
            time.sleep(30)
        except requests.exceptions.ConnectionError as err:
            randomtime = random.randint(0, 1)
            if connect_flag:
                logger.error('Connection Issue\n {} - Retrying in {} secs'.format(err, randomtime))
                connect_flag = False
            time.sleep(randomtime)
            continue
        except Exception as e:
            logger.debug(e, exc_info=True)


def run_flask(log_port, host_dir):
    logger = get_logger('flask')
    try:
        app = Flask(__name__, static_url_path="/files", static_folder=host_dir)
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        app.run(host='0.0.0.0', port=log_port, debug=False)
    except Exception as e:
        logger.debug(e, exc_info=True)


def main():
    logger = get_logger('main')
    concurrent_count, executable_command, tool, runner_id, machine_name, log_port, time_betw_jobs, host_dir, \
    data_retain = runner_details()
    try:
        if check_queue_server_status():
            update_runner = Thread(target=post_status,
                                   args=(runner_id, tool, machine_name, concurrent_count, log_port))

            flask_data = Thread(target=run_flask, args=(log_port, host_dir))

            logger.info("Starting Thread For Server Coordination")
            update_runner.start()
            time.sleep(1)

            logger.info("Starting Thread For Hosting Reports/Logs")
            flask_data.start()
            time.sleep(1)

            logger.info("Starting Execution Threads")
            get_avail_project(concurrent_count, runner_id, tool, executable_command, time_betw_jobs)
            update_runner.join()
            flask_data.join()

    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    main()
