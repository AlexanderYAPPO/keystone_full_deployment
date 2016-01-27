# -*- coding: utf-8 -*-
import json
import os
import matplotlib
import getpass
matplotlib.use('Agg')  # fix "no $DISPLAY" and "no display name" errors
from numpy import array
from scipy import stats
from subprocess import Popen, PIPE, check_output

THRESHOLD = 0.01
TIMES = 120
DEP_NAME = "existing"
HOME_DIR = "/home/%s" % getpass.getuser()
RALLY_PATH = "%s/rally/bin/rally" % HOME_DIR


class DegradationCheck:
    def __init__(self, fs, db, srv):
        home_dir = "/home/%s" % getpass.getuser()
        self.id_dict = {}  # {rps : id}
        self.results_dir = "%s/results/%s/%s/%s" % (home_dir,
                                                    fs.replace("/", ""),
                                                    db,
                                                    srv
                                                    )

    def create_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def lin_regress(self, tmp_x, tmp_y, n_errors):
        if n_errors != 0:
            return True
        if not len(tmp_x) or not len(tmp_y):
            return False
        x_arr = array(tmp_x)
        y_arr = array(tmp_y)
        a = stats.linregress(x_arr, y_arr)[0]  # getting slope
        with open(self.results_dir + '/sk_iters.txt', 'a') as f:
            f.write("a: %s, errors: %s\n" % (a, n_errors))
        if a > THRESHOLD:
            return True
        return False

    def update_rps(self, rps):
        context = {}
        runner = {}
        context["project_domain"] = "default"
        context["resource_management_workers"] = 1
        context["tenants"] = 1
        context["user_domain"] = "default"
        context["users_per_tenant"] = 1
        runner["rps"] = int(rps)
        runner["times"] = int(rps * TIMES)
        runner["type"] = "rps"
        task_dict = {"Authenticate.keystone": [{
            "context": {"users": context},
            "runner": runner
            }]}
        with open(HOME_DIR + "/nfind.json", 'wb') as outfile:
            json.dump(task_dict, outfile)

    def get_results(self, rps):
        self.update_rps(rps)  # rps changing
        p1 = Popen([RALLY_PATH, "deployment", "use", DEP_NAME], stdout=PIPE)
        p1.wait()
        p2 = Popen([RALLY_PATH,
                    "--noverbose",
                    "task",
                    "start",
                    HOME_DIR + "/nfind.json"],
                   stdout=PIPE)
        p2.wait()
        txt = p2.communicate()[0].decode("utf-8")
        if "task results" not in txt:
            return (False, False)
        id = txt.split("rally task results ")[1].replace("\n", "")
        result = check_output("%s task results %s" % (RALLY_PATH, id),
                              shell=True
                              )
        return (id, result.decode("utf-8"))

    def save_results(self, rps):
        if rps in self.id_dict:
            id = self.id_dict[rps]
        json_data = check_output("%s task results %s" % (RALLY_PATH, id),
                                 shell=True).decode("utf-8")
        with open(self.results_dir + '/%s_j.json' % rps, 'wb') as outfile:
            json.dump(json_data, outfile)
        report_args = (RALLY_PATH, id, self.results_dir + '/%s_h.html' % rps)
        check_output("%s task report %s --out %s" % report_args, shell=True)

    def is_degradation(self, rps):
        print "="*10
        print "rps: ", rps
        print "="*10
        self.create_dir(self.results_dir)
        id, json_data = self.get_results(rps)
        if not id:
            return True
        self.id_dict[rps] = id
        tmp_x = []
        tmp_y = []
        full_json = json.loads(json_data)[0]
        t1 = full_json["result"][0]["timestamp"]
        n_errors = 0
        iter = 0
        for result in full_json["result"]:
            t2 = result["timestamp"] - t1
            if t2 > 60:
                tmp_x.append(result["timestamp"])
                tmp_y.append(float(result["duration"]))
            else:
                iter += 1
            if len(result["error"]) != 0:
                n_errors += 1
        with open(self.results_dir + '/sk_iters.txt', 'a') as f:
            f.write("N=%s: first %s iterations skipped, err: %s\n" % (rps,
                                                                      iter,
                                                                      n_errors
                                                                      ))
        return self.lin_regress(tmp_x, tmp_y, n_errors)

