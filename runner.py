#!/usr/bin/env python
import os
import getpass
from sys import argv
from ansible.playbook import PlayBook
from ansible import callbacks
from ansible import utils
from degr import DegradationCheck

USERNAME = getpass.getuser()  # current user's username
PASSWORD = getpass.getpass()  # sudo pasword

WEB_SERVERS = ["apache", "uwsgi"]
DBMS = ["postgresql", "mysql"]  # database type
FS = ("/dev/sda7",  # HDD
          "tmpfs",  # overlay
          "/dev/sdb1"  # SSD
          )

class extra():
    def __init__(self, db = None, fs = None, srv = None):
        self.db = db
        self.srv = srv
        self.fs = fs


class t:
    def __init__(self, action, name, extra):
        self.action = action
        self.name = name
        self.extra = extra


class GE:
    def __init__(self, act):
        self.i = 0
        self.L = []
        if act == "install":
            LIST = [
                t("install", "tests", extra()),
                t("install", "postgresql", extra()),
                t("install", "mysql", extra()),
                t("install", "keystone", extra()),
                t("install", "apache", extra()),
                t("install", "uwsgi", extra()),
                t("install", "rally", extra())
                ]
            task = {"list": LIST}
            self.L.append(task)

        if act == "run":
            for db in DBMS:
                for srv in WEB_SERVERS:
                    for fs in FS:
                        LIST =  [
<<<<<<< HEAD
                                t("stop", db, {}),
                                t("stop", srv, {}),
                                t("mount", fs, {"db": db}),
                                t("run", db, {}),
                                t("run", srv, {"db": db}),
                                #t("func", "tests", {"db": db, "fs": fs, "srv": srv}),
                                t("stop", srv, {}),
                                t("stop", db, {}),
                                t("umount", db, {"db": db}),
                                t("stop", "rally", {})
=======
                                t("stop", db, extra()),
                                t("stop", srv, extra()),
                                t("mount", fs, extra(db)),
                                t("run", db, extra(db)),
                                t("run", srv, extra(db)),
                                t("func", "tests",extra(fs,db,srv)),
                                t("stop", srv, extra()),
                                t("stop", db, extra()),
                                t("umount", db, extra()),
                                t("stop", "rally", extra())
>>>>>>> 15a4e600e55ee34b01bba9dd5a03811a9bb0acf5
                                ]
                        task = {"list": LIST,
                                "param1": 0,
                                "param2": 200
                        }
                        self.L.append(task)
        self.n = len(self.L)

    def get_savetask(self):
        cur = self.i - 1
        for index, item in enumerate(self.L[cur]["list"]):
            if item.name == "tests":
                item.name = "save"
                self.L[cur]["list"][index] = item
        return self.L[cur]

    def __iter__(self):
        return self

    def next(self):
        if self.i < self.n:
            i = self.i
            self.i += 1
            return self.L[i]
        else:
            raise StopIteration()



def run_playbook(name, extra):
    utils.VERBOSITY = 0
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    stats = callbacks.AggregateStats()
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats,
                                                  verbose=utils.VERBOSITY)
    pb = PlayBook(
        playbook='/home/%s/keystone_full_deployment/ansible/%s.yml'
                 % (USERNAME, name),
        host_list="/home/%s/keystone_full_deployment/ansible/hosts"% USERNAME,
        remote_user=USERNAME,
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        private_key_file='/home/%s/.ssh/id_rsa' % USERNAME,
        become=True,
        become_pass="%s\n" % PASSWORD,
        become_method='sudo',
        extra_vars=extra
    )
    results = pb.run()
    playbook_cb.on_stats(pb.stats)
    return results

def read_json(rps, db, fs, srv):
    d = DegradationCheck(fs.replace("/", ""), db, srv)
    isdeg = d.read_json(rps)
    return isdeg

def save(rps, db, fs, srv):
    d = DegradationCheck(fs.replace("/", ""), db,srv)
    d.read_json(rps)
    d.save_results(rps)
    print "saved", rps, db, fs, srv

class Runner:
    def __init__(self, task):
        self.LIST = task["list"]
        self.rps = None
 
    def parse(self, task):
        action = task.action
        name = task.name
        params = {}
        if action == "mount" or action == "umount":
            fs_type = "tmpfs" if name == "tmpfs" else "ext4"
            params = {"fs_src" : name, "fs_type": fs_type}
            db = task.extra.db
            if db == "postgresql":
                run_playbook("%s_postgresql" % action, params)
            if db == "mysql":
                run_playbook("%s_mysql" % action, params)
        if action == "stop" or action == "install":
            run_playbook("%s_%s" % (action, name), params)
        if action == "run":
            if name in WEB_SERVERS:
                params = {"global_db" : task.extra.db}
            run_playbook("%s_%s" % (action, name), params)

        if action == "func":
            if name == "tests":
                rps = self.rps
                return read_json(rps, task.extra.db, task.extra.fs, task.extra.srv)
            if name == "save":
                rps = self.rps
                return save(rps, task.extra.db, task.extra.fs, task.extra.srv)


    def execute(self):
        result = None
        for task in self.LIST:
            res = self.parse(task)
            if res != None:
                result = res
        print "executed:"
        print [(x.action, x.name) for x in self.LIST]
        return result



def bin_search(task):
    left = task["param1"]
    right = task["param2"]
    while True:
        m = int((left + right) / 2)
        runner.rps = m
        result = runner.execute()
        if result:
            right = m
        else:
            left = m
        if right == left + 1:
            return left


def cmd_parse():
    return 1

if __name__ == "__main__":
    inst = cmd_parse()
    if inst:
        install_gen = GE("install")
        for task in install_gen:
            runner = Runner(task)
            runner.execute()

    run_gen = GE("run")
    for task in run_gen:
        runner = Runner(task)
        N = bin_search(task)
        print "N = %s" % N
        save_task = run_gen.get_savetask()
        for rps in (N - 1, N, N + 1, N + 3, N + 5, 2 * N):
            save_runner = Runner(save_task)
            save_runner.rps = rps
            save_runner.execute()
        #Runner({"list": [t("install", "rally")]}).execute()
