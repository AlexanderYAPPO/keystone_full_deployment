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
# 1
class extra(): 
    def __init__(self, db = None, fs = None, srv = None, param1 = 0, param2 = 0):
        self.db = db
        self.srv = srv
        self.fs = fs
        self.param1 = param1
        self.param2 = param2


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
            self.L.append(LIST)

        if act == "run":
            for db in DBMS:
                for srv in WEB_SERVERS:
                    for fs in FS:
                        LIST =  [
                                t("stop", db, extra()),
                                t("stop", srv, extra()),
                                t("mount", fs, extra(db)),
                                t("run", db, extra(db)),
                                t("run", srv, extra(db)),
                                t("func", "tests",extra(fs,db,srv, 0, 200)),
                                t("stop", srv, extra()),
                                t("stop", db, extra()),
                                t("umount", db, extra()),
                                t("stop", "rally", extra())
                                ]
                        self.L.append(LIST)
        self.n = len(self.L)

    def get_savetask(self):
        L = []
        for db in DBMS:
            for srv in WEB_SERVERS:
                for fs in FS:
                    LIST =  [
                            t("stop", db, extra()),
                            t("stop", srv, extra()),
                            t("mount", fs, extra(db)),
                            t("run", db, extra(db)),
                            t("run", srv, extra(db)),
                            t("func", "save",extra(fs,db,srv, 0, 200)),
                            t("stop", srv, extra()),
                            t("stop", db, extra()),
                            t("umount", db, extra()),
                            t("stop", "rally", extra())
                            ]
        self.n = len(L)
        return L

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



class Runner:
    def __init__(self, task):
        self.task = task
        self.rps = None
 
    def run(self):
        task = self.task
        action = task.action
        name = task.name
        params = {}
        if action == "mount":
            fs_type = "tmpfs" if name == "tmpfs" else "ext4"
            params = {"fs_src" : name, "fs_type": fs_type}
            db = task.extra.db
            if db == "postgresql":
                run_playbook("mount_postgresql", params)
            if db == "mysql":
                run_playbook("mount_mysql", params)
        if action == "stop" or action == "install":
            run_playbook("%s_%s" % (action, name), params)
        if action == "run":
            if name in WEB_SERVERS:
                params = {"global_db" : task.extra.db}
            run_playbook("%s_%s" % (action, name), params)

        if action == "func":
            if name == "tests":
                rps = self.rps
                d = DegradationCheck(task.extra.fs.replace("/", ""), task.extra.db, task.extra.srv)
                isdeg = d.read_json(self.rps)
                return isdeg
            if name == "save":
                rps = self.rps
                d = DegradationCheck(task.extra.fs.replace("/", ""), task.extra.db, task.extra.srv)
                d.read_json(self.rps)
                d.save_results(self.rps)


def bin_search(L, param1, param2):
    left = param1
    right = param2
    while True:
        m = int((left + right) / 2)
        degr = None
        for obj in L:
            runner = Runner(obj)
            if obj.name == "tests":
                runner.rps = m
                degr = runner.run()
            else:
                runner.run()

        if degr:
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
        for L in install_gen:
            for obj in L:
                runner = Runner(obj)
                runner.run()
    run_gen = GE("run")
    for L in run_gen:
        for obj in L:
            runner = Runner(obj)
            if obj.name == "tests": 
                N = bin_search(L, obj.extra.param1, obj.extra.param2) # 2
                print "N = %s" % N
                save_task = run_gen.get_savetask()
                for save_obj in save_task:
                    save_runner = Runner(save_obj)
                    if save_obj.name == "save":
                        for rps in (N - 1, N, N + 1, N + 3, N + 5, 2 * N):
                            save_runner.rps = rps
                            save_runner.run()
                    else:
                        save_runner.run()
            else:
                runner.run()

