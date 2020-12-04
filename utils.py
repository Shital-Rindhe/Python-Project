import json
import os
import socket
import subprocess
import time
from configparser import ConfigParser
from threading import Thread

import requests

from constants import HEADERS, CONFIG_FILE, URL, SCRIPT
from logger import get_logger, get_log_path

logger = get_logger('utils')


def runner_details():
    try:
        config = ConfigParser()
        config.read(CONFIG_FILE)
        concurrent_count = config.get('RUNNER_SETTINGS', 'CONCURRENT_COUNT')
        executable_path = config.get('RUNNER_SETTINGS', 'EXECUTABLE_COMMAND')
        tool = config.get('RUNNER_SETTINGS', 'TOOL')
        log_port = config.get('RUNNER_SETTINGS', 'LOG_PORT')
        time_betw_jobs = config.get('RUNNER_SETTINGS', 'TIME_BETWEEN_JOBS')
        host_dir = config.get('HOSTED_DIR_SETTINGS', 'HOSTED_DIR')
        data_retain = config.get('HOSTED_DIR_SETTINGS', 'DATA_RETENTION')

        machine_name = socket.gethostname()

        if "-" in machine_name:
            machine_no = machine_name.strip().split("-", 1)
            machine_no = machine_no[1].strip()
        else:
            machine_no = machine_name.strip()

        runner_id = "K" + tool[:2] + machine_no

        return concurrent_count, executable_path, tool, runner_id, machine_name, log_port, time_betw_jobs, \
               host_dir, data_retain
    except Exception as e:
        logger.error("Issue Reading Config File")
        logger.debug(e, exc_info=True)


def get_log_dir():
    concurrent_count, executable_command, tool, runner_id, machine_name, log_port, time_betw_jobs, host_dir, \
    data_retain = runner_details()
    log_path = os.path.join(host_dir, "logs")
    report_path = os.path.join(host_dir, "Reports")
    os.makedirs(log_path, exist_ok=True)
    os.makedirs(report_path, exist_ok=True)
    return log_path


def get_log_file(db_id):
    out_file = os.path.join(get_log_dir(), str(db_id) + '.txt')
    return out_file


def check_gitlab_status(prc, db_id, api_token, url):
    while True:
        try:
            r = requests.get(url, headers={'PRIVATE-TOKEN': api_token, 'Accept': 'application/json'})
        except:
            continue

        if r.json().get('status') != 'running' and r.status_code == 200:
            requests.patch(
                URL + "toolqueue/projects/setstatusdash/" + str(db_id) + "?statusId=5",
                headers=HEADERS)
            prc.kill()
            cmd = '"' + SCRIPT + '"' + ' ' + str(db_id)
            clear_data = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            clear_data.wait()
            return
        time.sleep(5)
        poll = prc.poll()
        if poll is not None:
            break


def print_output(prc, db_id):
    for line in prc.stdout:
        # write in log file
        with open(get_log_file(db_id), 'a+') as file:
            file.write(line.decode().strip() + "\n")
        poll = prc.poll()
        if poll is not None:
            break


def run_tool(json_file_path, db_id, commit_id, job_id, executable_command, runner_id, index, time_betw_jobs,
             gitlab_check_url, api_token):
    cmd = executable_command + ' ' + json_file_path + ' ' + str(db_id) + ' ' + str(commit_id) + ' ' + str(job_id)

    try:
        # try:
        #     r = requests.get(gitlab_check_url, headers={'PRIVATE-TOKEN': api_token, 'Accept': 'application/json'})
        # except Exception as e:
        #     logger.debug(e, exc_info=True)
        r = requests.get(gitlab_check_url, headers={'PRIVATE-TOKEN': api_token, 'Accept': 'application/json'})

        if r.json().get('status') == 'running' or r.status_code != 200:

            prc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            check_thread = Thread(target=check_gitlab_status,
                                  args=(prc, db_id, api_token, gitlab_check_url))
            check_thread.start()

            output_process = Thread(target=print_output,
                                    args=(prc, db_id))
            output_process.start()

            prc.wait()
            check_thread.join()
            try:
                r = requests.get(gitlab_check_url, headers={'PRIVATE-TOKEN': api_token, 'Accept': 'application/json'})
            except Exception as e:
                logger.debug(e, exc_info=True)

            if r.json().get('status') == 'running' or r.status_code != 200:
                if prc.returncode == 0:
                    # 3 - Successful
                    status_code = 3
                    logger.info('Job Successful')
                    json_data = {"statusId": status_code, "exitCode": 0, "runnerId": runner_id + "-" + index}
                    requests.patch(URL + "toolqueue/projects/setstatus/" + str(db_id),
                                   json=json_data,
                                   headers=HEADERS)
                    logger.info("Status Updated As SUCCESSFUL")

                else:
                    # 4 - Failed
                    status_code = 4
                    logger.info('Job Failed With Exit Code ' + str(prc.returncode))
                    json_data = {"statusId": status_code, "exitCode": prc.returncode,
                                 "runnerId": runner_id + "-" + index}
                    requests.patch(URL + "toolqueue/projects/setstatus/" + str(db_id),
                                   json=json_data,
                                   headers=HEADERS)
                    logger.info("Status Updated As FAILED")
            else:
                logger.info('Job Aborted From GitLab')
                logger.info("Status Updated As ABORTED")

        else:
            requests.patch(URL + "toolqueue/projects/setstatusdash/" + str(db_id) + "?statusId=5", headers=HEADERS)
            logger.info('Job Aborted From GitLab')
            logger.info("Status Updated As ABORTED")

    except Exception as e:
        logger.error("Issue In Tool Execution")
        logger.debug(e, exc_info=True)

    time.sleep(int(time_betw_jobs))


def write_json(db_id, json_data):
    json_path = os.path.join(get_log_path(), "json")
    os.makedirs(json_path, exist_ok=True)
    json_file_path = os.path.join(json_path, str(db_id) + '.txt')
    with open(json_file_path, 'w') as f:
        json.dump(json_data, f)
    return json_file_path


def process_data(data, index, runner_id, executable_command, time_betw_jobs):
    config_data = data['configJson']
    job_id = data['jobId']
    commit_id = data['commitId']
    db_id = data['id']
    api_url = data['apiUrl']
    git_project_id = data['gitProjectId']
    api_token = data['apiToken']

    logger.info("Received Project For ID " + str(db_id) + " By Executor-" + str(index))

    try:
        json_data = {"statusId": 2, "runnerId": runner_id + "-" + index}
        r = requests.patch(URL + "toolqueue/projects/setstatus/" + str(db_id),
                           json=json_data, headers=HEADERS)
        if r.status_code == 200:
            try:
                json_file_path = write_json(db_id, config_data)
                logger.info("Status Updated As IN PROGRESS")
                gitlab_check_url = api_url + '/projects/' + git_project_id + '/jobs/' + job_id
                run_tool(json_file_path, db_id, commit_id, job_id, executable_command, runner_id, index, time_betw_jobs,
                         gitlab_check_url, api_token)
            except Exception as e:
                logger.error("Issue With Json File")
                logger.debug(e, exc_info=True)

    except Exception as e:
        logger.debug(e, exc_info=True)
