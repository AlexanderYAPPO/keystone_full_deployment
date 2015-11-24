# -*- coding: utf-8 -*-
import json
import os
import sys
import matplotlib
matplotlib.use('Agg')  # fix "no $DISPLAY" and "no display name" errors
from numpy import array
from scipy import stats
from subprocess import Popen, PIPE, check_output

UPPER_BOUND = 20  # of the binary search
THRESHOLD = 0.01
TIMES = 120

os_user = sys.argv[1]
test_num = sys.argv[2]

home_dir = "/home/%s" % os_user
rally_path = "%s/rally/bin/rally" % home_dir
results_dir = home_dir + "/results/" + str(test_num)

ID_DICT = {}  # {rps : id}

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def is_degr(tmp_X, tmp_Y, n_errors):
    if n_errors != 0:
        return True
    X = array(tmp_X)
    Y = array(tmp_Y)
    a = stats.linregress(X, Y)[0]  # getting slope
    if a > THRESHOLD:
        return True
    return False


def update_rps(rps):
    d = {"Authenticate.keystone" : [{}]}
    d["Authenticate.keystone"][0]["context"] = {}
    d["Authenticate.keystone"][0]["context"]["users"] = {}
    d["Authenticate.keystone"][0]["context"]["users"]["project_domain"] = "default"
    d["Authenticate.keystone"][0]["context"]["users"]["resource_management_workers"] = 30
    d["Authenticate.keystone"][0]["context"]["users"]["tenants"] = 1
    d["Authenticate.keystone"][0]["context"]["users"]["user_domain"] = "default"
    d["Authenticate.keystone"][0]["context"]["users"]["users_per_tenant"] = 1
    d["Authenticate.keystone"][0]["runner"] = {}
    d["Authenticate.keystone"][0]["runner"]["rps"] = int(rps)
    d["Authenticate.keystone"][0]["runner"]["TIMES"] = int(rps * TIMES)
    d["Authenticate.keystone"][0]["runner"]["type"] = "rps"
    with open(home_dir + "/nfind.json", 'wb') as outfile:
        json.dump(d, outfile)

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
    result = check_output("%s task results %s" % (rally_path, id), shell=True)

    return (id, result.decode("utf-8"))


def save_results(rps):
    id = ID_DICT[rps]
    json_data = get_results(rps)[1]
    with open(results_dir + '/%s_j.json' % rps, 'wb') as outfile:
        json.dump(json_data, outfile)
    report_args = (rally_path, id, results_dir + '/%s_h.html' % rps)
    check_output("%s task report %s --out %s" % report_args, shell=True)


def read_json(rps, save):
    id, json_data = get_results(rps)
    ID_DICT[rps] = id
    if save:
        save_results(rps)
    tmp_X = []
    tmp_Y = []
    n_errors = 0
    full_json = json.loads(json_data)[0]
    for result in full_json["result"]:
        tmp_X.append(result["TIMEStamp"])
        tmp_Y.append(float(result["duration"]))
        if len(result["error"]) != 0:
            n_errors += 1
    return is_degr(tmp_X, tmp_Y, n_errors)


def bin_search():
    left = 1
    rigth = UPPER_BOUND
    m = UPPER_BOUND / 2
    while True:
        m = int((left + rigth) / 2)
        if r(m):
            rigth = m
        else:
            left = m + 1
        if left == rigth:
            return m


if __name__ == "__name__":
    create_dir("%s/results" % home_dir)
    create_dir(results_dir)
    N = bin_search()
    read_json(N - 1, True)
    save_results(N)
    read_json(N + 1, True)
    read_json(2 * N, True)
    read_json(3 * N, True)
    read_json(10 * N, True)

