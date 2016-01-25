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
BACKENDS = ["postgresql", "mysql"]  # database type
HARDWARE = ("/dev/sda7",  # HDD
            "tmpfs",  # overlay
            "/dev/sdb1"  # SSD
            )


class Extra():
    def __init__(self, db=None, fs=None, srv=None, param1=0, param2=0):
        self.db = db
        self.srv = srv
        self.fs = fs
        self.param1 = param1
        self.param2 = param2

    def get_savetask(self):
        if keystone_type == "mock":
            run_obj = t("run", "mock", Extra())
        else:
            run_obj = t("run", self.srv, Extra(self.db))
        if keystone_type == "mock":
            stop_obj = t("stop", "mock", Extra())
        else:
            stop_obj = t("stop", self.srv, Extra())
        new_list = [
                t("stop", self.db, Extra()),
                t("stop", self.srv, Extra()),
                t("mount", self.fs, Extra(self.db)),
                t("run", self.db, Extra(self.db)),
                run_obj,
                t("func", "save", Extra(self.db, self.fs, self.srv, 0, 1000)),
                stop_obj,
                t("stop", self.db, Extra()),
                t("umount", self.db, Extra(self.db)),
                t("stop", "rally", Extra())
                ]
        return new_list


class t:
    def __init__(self, action, name, extra):
        self.action = action
        self.name = name
        self.extra = extra


class Generator:
    def __init__(self, act):
        self.i = 0
        self.L = []
        if act == "install":
            LIST = [
                t("install", "tests", Extra()),
                t("install", "postgresql", Extra()),
                t("install", "mysql", Extra()),
                t("install", "keystone", Extra()),
                t("install", "apache", Extra()),
                t("install", "uwsgi", Extra()),
                t("install", "rally", Extra()),
                t("install", "mock", Extra())
                ]
            self.L.append(LIST)

        if act == "run":
            for db in BACKENDS:
                for srv in WEB_SERVERS:
                    for fs in HARDWARE:
                        if keystone_type == "mock":
                            run_obj = t("run", "mock", Extra())
                        else:
                            run_obj = t("run", self.srv, Extra(self.db))
                        if keystone_type == "mock":
                            stop_obj = t("stop", "mock", Extra())
                        else:
                            stop_obj = t("stop", self.srv, Extra())
                        LIST = [
                            t("stop", db, Extra()),
                            t("stop", srv, Extra()),
                            t("mount", fs, Extra(db)),
                            t("run", db, Extra(db)),
                            run_obj,
                            t("func", "tests", Extra(db, fs, srv, 0, 1000)),
                            stop_obj,
                            t("stop", db, Extra()),
                            t("umount", db, Extra(db)),
                            t("stop", "rally", Extra())
                                ]
                        self.L.append(LIST)
        self.n = len(self.L)

    def __iter__(self):
        return self

    def next(self):
        if self.i < self.n:
            i = self.i
            self.i += 1
            return self.L[i]
        else:
            raise StopIteration()


def run_playbook(name, params):
    utils.VERBOSITY = 0
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    stats = callbacks.AggregateStats()
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats,
                                                  verbose=utils.VERBOSITY)
    pb = PlayBook(
        playbook='/home/%s/keystone_full_deployment/ansible/%s.yml'
                 % (USERNAME, name),
        host_list="/home/%s/keystone_full_deployment/ansible/hosts" % USERNAME,
        remote_user=USERNAME,
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        private_key_file='/home/%s/.ssh/id_rsa' % USERNAME,
        become=True,
        become_pass="%s\n" % PASSWORD,
        become_method='sudo',
        extra_vars=params
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
        if action == "mount" or action == "umount":
            fs_type = "tmpfs" if name == "tmpfs" else "ext4"
            params = {"fs_src": name, "fs_type": fs_type}
            db = task.extra.db
            run_playbook("%s_%s" % (action, db), params)
        if action == "stop" or action == "install":
            run_playbook("%s_%s" % (action, name), params)
        if action == "run":
            if name in WEB_SERVERS:
                params = {"global_db": task.extra.db}
            run_playbook("%s_%s" % (action, name), params)

        if action == "func":
            extra = task.extra
            if name == "tests":
                rps = self.rps
                d = DegradationCheck(extra.fs, extra.db, extra.srv)
                isdeg = d.read_json(self.rps)
                return isdeg
            if name == "save":
                rps = self.rps
                d = DegradationCheck(extra.fs, extra.db, extra.srv)
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
    global keystone_type
    #keystone_type = "mock"
    keystone_type = "default"
    return 1


if __name__ == "__main__":
    inst = cmd_parse()
    if inst:
        install_gen = Generator("install")
        for L in install_gen:
            for obj in L:
                runner = Runner(obj)
                runner.run()
    run_gen = Generator("run")
    for L in run_gen:
        for obj in L:
            runner = Runner(obj)
            if obj.name == "tests":
                N = bin_search(L, obj.extra.param1, obj.extra.param2)
                print "N = %s" % N
                save_list = obj.extra.get_savetask()
                for rps in (N - 1, N, N + 1, N + 3, N + 5, 2 * N):
                    for save_obj in save_list:
                        save_runner = Runner(save_obj)
                        if save_obj.name == "save":
                                save_runner.rps = rps
                                save_runner.run()
                        else:
                            save_runner.run()
            else:
                runner.run()

