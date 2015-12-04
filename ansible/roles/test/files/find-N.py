# -*- coding: utf-8 -*-
import json
import os
import sys
import matplotlib
matplotlib.use('Agg')  # fix "no $DISPLAY" and "no display name" errors
from numpy import array
from scipy import stats
from subprocess import Popen, PIPE, check_output
from StringIO import StringIO
from threading  import Thread

UPPER_BOUND = 20  # of the binary search
THRESHOLD = 0.01
TIMES = 120
DEP_NAME = "existing"
OS_USER = sys.argv[1]
TEST_NUMB = sys.argv[2]

HOME_DIR = "/home/%s" % OS_USER
RALLY_PATH = "%s/rally/bin/rally" % HOME_DIR
RESULTS_DIR = HOME_DIR + "/results/" + str(TEST_NUMB)

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
    d = {"Authenticate.keystone": [{}]}
    d["Authenticate.keystone"][0]["context"] = {}
    d["Authenticate.keystone"][0]["context"]["users"] = {}
    d["Authenticate.keystone"][0]["context"]["users"]["project_domain"] = "default"
    d["Authenticate.keystone"][0]["context"]["users"]["resource_management_workers"] = 30
    d["Authenticate.keystone"][0]["context"]["users"]["tenants"] = 1
    d["Authenticate.keystone"][0]["context"]["users"]["user_domain"] = "default"
    d["Authenticate.keystone"][0]["context"]["users"]["users_per_tenant"] = 1
    d["Authenticate.keystone"][0]["runner"] = {}
    d["Authenticate.keystone"][0]["runner"]["rps"] = int(rps)
    d["Authenticate.keystone"][0]["runner"]["times"] = int(rps * TIMES)
    d["Authenticate.keystone"][0]["runner"]["type"] = "rps"
    with open(HOME_DIR + "/nfind.json", 'wb') as outfile:
        json.dump(d, outfile)

def tee(infile, *files):
    """Print `infile` to `files` in a separate thread."""
    def fanout(infile, *files):
        for line in iter(infile.readline, ''):
            for f in files:
                f.write(line)
        infile.close()
    t = Thread(target=fanout, args=(infile,)+files)
    t.daemon = True
    t.start()
    return t

def teed_call(cmd_args, **kwargs):    
    stdout, stderr = [kwargs.pop(s, None) for s in 'stdout', 'stderr']
    p = Popen(cmd_args,
              stdout=PIPE if stdout is not None else None,
              stderr=PIPE if stderr is not None else None,
              **kwargs)
    threads = []
    if stdout is not None: threads.append(tee(p.stdout, stdout, sys.stdout))
    if stderr is not None: threads.append(tee(p.stderr, stderr, sys.stderr))
    for t in threads: t.join() # wait for IO completion
    return p.wait()

def get_results(rps):
    update_rps(rps)  # rps changing
    p1 = Popen([RALLY_PATH, "deployment", "use", DEP_NAME], stdout=PIPE)
    p1.wait()


    fout, ferr = StringIO(), StringIO()
    exitcode = teed_call([RALLY_PATH,
                "task",
                "start",
                HOME_DIR + "/nfind.json"], stdout=fout, stderr=ferr)
    stdout = fout.getvalue()
    stderr = ferr.getvalue()
    #p2.wait()
    with open("%s/err_%s.txt" % (RESULTS_DIR, rps), "w") as f:
        f.write(stderr)
    #txt = p2.communicate()[0].decode("utf-8")
    txt = stdout
    if exitcode:
        return (False, False)
    #    sys.exit(1)
    id = txt.split("rally task results ")[1].replace("\n", "")
    result = check_output("%s task results %s" % (RALLY_PATH, id), shell=True)

    return (id, result.decode("utf-8"))


def save_results(rps):
    id = ID_DICT[rps]
    json_data = check_output("%s task results %s" % (RALLY_PATH, id), shell=True).decode("utf-8")
    with open(RESULTS_DIR + '/%s_j.json' % rps, 'wb') as outfile:
        json.dump(json_data, outfile)
    report_args = (RALLY_PATH, id, RESULTS_DIR + '/%s_h.html' % rps)
    check_output("%s task report %s --out %s" % report_args, shell=True)


def read_json(rps, save):
    id, json_data = get_results(rps)
    if id == False:
        return True
    ID_DICT[rps] = id
    if save:
        save_results(rps)
        return
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
    left = 1
    right = UPPER_BOUND
    m = UPPER_BOUND / 2
    while True:
        m = int((left + right) / 2)
        if read_json(m, False):
            right = m
        else:
            left = m
        if right == left + 1:
            return left


if __name__ == "__main__":
    create_dir("%s/results" % HOME_DIR)
    create_dir(RESULTS_DIR)
    N = bin_search()
    #read_json(N - 1, True)
    if not N in ID_DICT:
        sys.exit(1)
    save_results(N)
    read_json(N + 1, True)
    read_json(2 * N, True)
    read_json(3 * N, True)
    read_json(10 * N, True)

