# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')  # fix "no $DISPLAY" and "no display name" errors
from numpy import array
from scipy import stats
from getpass import getuser
from json import dump
from json import loads
from os import makedirs
from os import path
from subprocess import Popen
from subprocess import PIPE
#!/usr/bin/python
from subprocess import check_output

THRESHOLD = 0.01
TIMES = 360
DEP_NAME = "existing"


class DegradationCheck:
    def __init__(self, hardware, database, web_server):
        self.id_dict = {}  # {rps : id}
        user = getuser()
        self.home_dir = "/home/%s" % user
        self.rally_path = "%s/rally/bin/rally" % self.home_dir
        self.results_dir = "%s/results/%s/%s/%s" % (self.home_dir,
                                                    hardware.replace("/", ""),
                                                    database,
                                                    web_server
                                                    )

    def create_dir(self, resultsdir_path):
        if not path.exists(resultsdir_path):
            makedirs(resultsdir_path)

    def lin_regress(self, tmp_x, tmp_y):
        if not len(tmp_x) or not len(tmp_y):
            return False
        x_arr = array(tmp_x)
        y_arr = array(tmp_y)
        a = stats.linregress(x_arr, y_arr)[0]  # getting slope
        print "="*10
        print "a=", a
        print "="*10
        with open(self.results_dir + '/sk_iters.txt', 'a') as f:
            f.write("a= %s\n" % (a))
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
        runner["type"] = "rps"
        runner["rps"] = int(rps)
        runner["times"] = int(rps * TIMES)
        runner["type"] = "rps"
        #runner["max_cpu_count"] = 8
        #runner["max_concurrency"] = 8
        task_dict = {"Authenticate.keystone": [{
            "context": {"users": context},
            "runner": runner
            }]}
        with open(self.home_dir + "/nfind.json", 'wb') as outfile:
            dump(task_dict, outfile)

    def get_results(self, rps):
        self.update_rps(rps)  # rps changing
        p1 = Popen([self.rally_path, "deployment", "use", DEP_NAME], stdout=PIPE)
        p1.wait()
        p2 = Popen([self.rally_path,
                    "--noverbose",
                    "task",
                    "start",
                    self.home_dir + "/nfind.json"],
                   stdout=PIPE)
        p2.wait()
        txt = p2.communicate()[0].decode("utf-8")
        print "="*10
        print "rally task results"
        print "="*10
        if "task results" not in txt:
            return (False, False)
        id = txt.split("rally task results ")[1].replace("\n", "")
        result = check_output("%s task results %s" % (self.rally_path, id),
                              shell=True
                              )
        return (id, result.decode("utf-8"))

    def save_results(self, rps):
        if rps in self.id_dict:
            id = self.id_dict[rps]
        json_data = check_output("%s task results %s" % (self.rally_path, id),
                                 shell=True).decode("utf-8")

        json_fname = self.results_dir + '/%srps.json' % rps
        html_fname = self.results_dir + '/%srps.html' % rps
        with open(json_fname, 'wb') as outfile:
            dump(json_data, outfile)
        report_args = (self.rally_path, id, html_fname)
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
        full_json = loads(json_data)[0]
        t1 = full_json["result"][0]["timestamp"]
        iter = 0
        for result in full_json["result"]:
            t2 = result["timestamp"] - t1
            if t2 > 60:
                tmp_x.append(result["timestamp"])
                tmp_y.append(float(result["duration"]))
            else:
                iter += 1
            if len(result["error"]) != 0:
                with open(self.results_dir + '/sk_iters.txt', 'a') as f:
                    f.write("rps:%s. Errors.\n" % (rps))
                return True
        with open(self.results_dir + '/sk_iters.txt', 'a') as f:
            f.write("rps:%s: first %s iterations  skipped\n" % (rps, iter))
        return self.lin_regress(tmp_x, tmp_y)

