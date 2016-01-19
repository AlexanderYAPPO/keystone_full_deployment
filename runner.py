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


class t:
    def __init__(self, action, name):
        self.action = action
        self.name = name


class GE:
    def __init__(self, act):
        self.i = 0
        self.L = []
        if act == "install":
            LIST = [
                t("install", "tests"),
                t("install", "postgresql"),
                t("install", "mysql"),
                t("install", "keystone"),
                t("install", "apache"),
                t("install", "uwsgi"),
                t("install", "rally")
                ]
            task = {"list": LIST}
            self.L.append(task)

        if act == "run":
            for db in DBMS:
                for srv in WEB_SERVERS:
                    for fs in FS:
                        LIST =  [
                                t("stop", db),
                                t("stop", srv),
                                t("mount", fs),
                                t("run", db),
                                t("run", srv),
                                t("func", "tests"),
                                t("stop", srv),
                                t("stop", db),
                                t("umount", db),
                                t("stop", "rally")
                                ]
                        task = {"list": LIST,
                                "param1": 0,
                                "param2": 20
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

def read_json(rps, db, fs, srv): # zaglushka
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
        self.db = None
        self.fs = None
        self.srv = None
        for t in self.LIST:
            name = t.name
            if name in DBMS:
                self.db = name
            if name in FS:
                self.fs = name
            if name in WEB_SERVERS:
                self.srv = name


    def parse(self, task):
        action = task.action
        name = task.name
        params = {}
        if action == "mount":
            fs_type = "tmpfs" if name == "tmpfs" else "ext4"
            params = {"fs_src" : name, "fs_type": fs_type}
            if self.db == "postgresql":
                run_playbook("mount_postgresql", params)
            if self.db == "mysql":
                run_playbook("mount_mysql", params) 
        
        if action == "run" or action == "stop" or action == "install":
            params = {"global_db" : self.db}
            run_playbook("%s_%s" % (action, name), params)
        
        if action == "func":
            if name == "tests":
                rps = self.rps
                return read_json(rps, self.db, self.fs, self.srv)
            if name == "save":
                rps = self.rps                
                return save(rps, self.db, self.fs, self.srv)


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
    return 0

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

    

