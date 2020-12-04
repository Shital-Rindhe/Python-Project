import os
import time

from logger import get_log_path
from utils import runner_details

json_path = os.path.join(get_log_path(), "json")
concurrent_count, executable_command, tool, runner_id, machine_name, log_port, time_betw_jobs, host_dir, \
    data_retain = runner_details()

now = time.time()
old = now - int(data_retain) * 24 * 60 * 60


def delete_file():
    if os.path.exists(json_path):
        for f in os.listdir(json_path):
            path = os.path.join(json_path, f)
            if os.path.isfile(path):
                stat = os.stat(path)
                if stat.st_ctime < old:
                    os.remove(path)

    if os.path.exists(host_dir):
        for r, d, f in os.walk(host_dir):
            for file in f:
                path = os.path.join(r, file)
                if os.path.isfile(path):
                    stat = os.stat(path)
                    if stat.st_ctime < old:
                        os.remove(path)
