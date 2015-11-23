# -*- coding: utf-8 -*-
import json
import os
import sys
import matplotlib
matplotlib.use('Agg')  # fix "no $DISPLAY" and "no display name" errors
from numpy import array
from scipy import stats
from subprocess import Popen, PIPE, check_output

os_user = sys.argv[1]
test_num = sys.argv[2]

home_dir = "/home/%s" % os_user
rally_path = "%s/rally/bin/rally" % home_dir
results_dir = home_dir + "/results/" + str(test_num)
allowed_value = 0.01
times = 120

ID_DICT = {}  # {rps : [id, json_data]}


def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def is_degr(tmp_X, tmp_Y, n_errors):
    if n_errors != 0:
        return True
    X = array(tmp_X)
    Y = array(tmp_Y)
    a = stats.linregress(X, Y)[0]  # getting slope
    if a > allowed_value:
        return True
    return False


def update_rps(rps):
    with open(home_dir + "/nfind.json", 'r+') as settingsData:
        settings = json.load(settingsData)
        settings["Authenticate.keystone"][0]["runner"]["rps"] = int(rps)  # update rps
        settings["Authenticate.keystone"][0]["runner"]["times"] = int(rps * times)
        settingsData.seek(0)  # rewind to beginning of file
        settingsData.write(json.dumps(settings,
                                      indent=2,
                                      sort_keys=True))
        settingsData.truncate()


def get_results(rps):
    update_rps(rps)  # rps changing
    p1 = Popen([rally_path, "deployment", "use", "existing"], stdout=PIPE)
    p1.wait()
    p2 = Popen([rally_path,
                "task",
                "start",
                home_dir + "/nfind.json"],
               stdout=PIPE)
    p2.wait()
    txt = p2.communicate()[0].decode("utf-8")
    id = txt.split("rally task results ")[1].replace("\n", "")
    result2 = check_output("%s task results %s" % (rally_path, id), shell=True)

    return (id, result2.decode("utf-8"))


def save_results(rps):
    id, json_data = ID_DICT[rps]
    with open(results_dir + '/%s_j.json' % rps, 'wb') as outfile:
        json.dump(json_data, outfile)
    report_args = (rally_path, id, results_dir + '/%s_h.html' % rps)
    check_output("%s task report %s --out %s" % report_args, shell=True)


def read_json(rps, save):
    id, json_data = get_results(rps)
    ID_DICT[rps] = [id, json_data]
    if save:
        save_results(rps)
    tmp_X = []
    tmp_Y = []
    n_errors = 0
    full_json = json.loads(json_data)[0]
    for result in full_json["result"]:
        tmp_X.append(result["timestamp"])
        tmp_Y.append(float(result["duration"]))
        if len(result["error"]) != 0:
            n_errors += 1
    return is_degr(tmp_X, tmp_Y, n_errors)


def bin_search():
    upper_bound = 20
    m = upper_bound / 2
    left = 1
    rigth = upper_bound
    while left <= rigth:
        if read_json(m, False):
            rigth = m - 1
        else:
            left = m + 1
        m = int((left + rigth) / 2)
    return m


create_dir("%s/results" % home_dir)
create_dir(results_dir)

N = bin_search()

read_json(N - 1, True)
save_results(N)
read_json(N + 1, True)
read_json(2 * N, True)
read_json(3 * N, True)
read_json(10 * N, True)

