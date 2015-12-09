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
    def __init__(self, params):
        home_dir = "/home/%s" % getpass.getuser()
        self.params = params
        self.ID_DICT = {}  # {rps : id}
        self.results_dir = "%s/results/%s/%s/%s" % (home_dir,
                                               self.params["global_fs_src"].replace("/",""),
                                               self.params["global_db"],
                                               self.params["global_run_type"])

    def create_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)


    def is_degr(self, tmp_X, tmp_Y, n_errors):
        if n_errors != 0:
            return True
        X = array(tmp_X)
        Y = array(tmp_Y)
        a = stats.linregress(X, Y)[0]  # getting slope
        print (a, THRESHOLD)
        if a > THRESHOLD:
            return True
        return False


    def update_rps(self, rps):
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


    def get_results(self, rps):
        self.update_rps(rps)  # rps changing
        p1 = Popen([RALLY_PATH, "deployment", "use", DEP_NAME], stdout=PIPE)
        p1.wait()
        p2 = Popen([RALLY_PATH,
                    "task",
                    "start",
                    HOME_DIR + "/nfind.json"],
                   stdout=PIPE)
        p2.wait() 
        txt = p2.communicate()[0].decode("utf-8")
        if not "task results" in txt:
            return (False, False)
        id = txt.split("rally task results ")[1].replace("\n", "")
        result = check_output("%s task results %s" % (RALLY_PATH, id), shell=True)

        return (id, result.decode("utf-8"))


    def save_results(self, rps):
        id = self.ID_DICT[rps]
        if id == False:
            with open(self.results_dir + '/%s_fail.txt' % rps, 'wb') as outfile:
                outfile.write("fail")
            return
        json_data = check_output("%s task results %s" % (RALLY_PATH, id), shell=True).decode("utf-8")
        with open(self.results_dir + '/%s_j.json' % rps, 'wb') as outfile:
            json.dump(json_data, outfile)
        report_args = (RALLY_PATH, id, self.results_dir + '/%s_h.html' % rps)
        check_output("%s task report %s --out %s" % report_args, shell=True)


    def read_json(self, rps):
        if len(self.params) > 0:
            self.create_dir(self.results_dir)
        id, json_data = self.get_results(rps)
        if id == False:
            return True
        self.ID_DICT[rps] = id
        #self.save_results(rps)
        tmp_X = []
        tmp_Y = []
        n_errors = 0
        full_json = json.loads(json_data)[0]
        for result in full_json["result"]:
            tmp_X.append(result["timestamp"])
            tmp_Y.append(float(result["duration"]))
            if len(result["error"]) != 0:
                n_errors += 1
        return self.is_degr(tmp_X, tmp_Y, n_errors)



