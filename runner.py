#!/usr/bin/env python
import os
import getpass
import argparse
from sys import argv
from ansible.playbook import PlayBook
from ansible import callbacks
from ansible import utils
from degr import DegradationCheck

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


class t:
    def __init__(self, action, name, extra):
        self.action = action
        self.name = name
        self.extra = extra


class Generator:
    def __init__(self, act):
        self.i = 0
        self.gen_list = []
        if act == "install":
            new_list = [
                t("install", "tests", Extra()),
                t("install", "postgresql", Extra()),
                t("install", "mysql", Extra()),
                t("install", "keystone", Extra()),
                t("install", "apache", Extra()),
                t("install", "uwsgi", Extra()),
                t("install", "rally", Extra()),
                t("install", "mock", Extra())
                ]
            self.gen_list.append(new_list)

        elif act == "default":
            for db in BACKENDS:
                for srv in WEB_SERVERS:
                    for fs in HARDWARE:
                        new_list = [
                            t("stop", db, Extra()),
                            t("stop", srv, Extra()),
                            t("mount", fs, Extra(db)),
                            t("run", db, Extra(db)),
                            t("run", srv, Extra(db)),
                            t("func", "tests", Extra(db, fs, srv, 0, 200)),
                            t("stop", srv, Extra()),
                            t("stop", db, Extra()),
                            t("umount", db, Extra(db)),
                            t("stop", "rally", Extra())
                            ]
                        self.gen_list.append(new_list)

        elif act == "mock":
            new_list = [
                t("run", "mock", Extra()),
                t("func", "tests", Extra("flask", "flask", "flask", 0, 1000)),
                t("stop", "mock", Extra()),
                t("stop", "rally", Extra())
                ]
            self.gen_list.append(new_list)
        self.n = len(self.gen_list)

    def __iter__(self):
        return self

    def next(self):
        if self.i < self.n:
            i = self.i
            self.i += 1
            return self.gen_list[i]
        else:
            raise StopIteration()


class Runner:
    def __init__(self, task):
        self.task = task
        self.rps = None

    def run(self):
        task = self.task
        action = task.action
        name = task.name
        extra = task.extra
        params = {}
        if action == "mount" or action == "umount":
            fs_type = "tmpfs" if name == "tmpfs" else "ext4"
            params = {
                "fs_src": name,
                "fs_type": fs_type
                }
            self.run_playbook("%s_%s" % (action, extra.db), params)
        elif action == "stop" or action == "install":
            self.run_playbook("%s_%s" % (action, name), params)
        elif action == "run":
            if name in WEB_SERVERS:
                params = {"global_db": extra.db}
            self.run_playbook("%s_%s" % (action, name), params)
        elif action == "func":
            if name == "tests":
                rps = self.rps
                d = DegradationCheck(extra.fs, extra.db, extra.srv)
                isdeg = d.read_json(self.rps)
                return isdeg
            elif name == "save":
                rps = self.rps
                d = DegradationCheck(extra.fs, extra.db, extra.srv)
                d.read_json(self.rps)
                d.save_results(self.rps)

    def run_playbook(self, name, params):
        utils.VERBOSITY = 0
        playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
        stats = callbacks.AggregateStats()
        runner_cb = callbacks.PlaybookRunnerCallbacks(stats,
                                                      verbose=utils.VERBOSITY)
        pb = PlayBook(
            playbook='/home/%s/keystone_full_deployment/ansible/%s.yml'
                     % (USER, name),
            host_list="/home/%s/keystone_full_deployment/ansible/hosts" % USER,
            remote_user=USER,
            callbacks=playbook_cb,
            runner_callbacks=runner_cb,
            stats=stats,
            private_key_file='/home/%s/.ssh/id_rsa' % USER,
            become=True,
            become_pass="%s\n" % PASSWORD,
            become_method='sudo',
            extra_vars=params
        )
        results = pb.run()
        playbook_cb.on_stats(pb.stats)
        return results


def save_func(n, cur_list):
    save_list = cur_list
    for rps in (n - 1, n, n + 1, n + 3, n + 5, 2 * n):
        for obj in save_list:
            runner = Runner(obj)
            if obj.name == "tests":
                runner = Runner(t("func", "save", obj.extra))
                runner.rps = rps
            runner.run()


def bin_search(cur_list):
    while True:
        for obj in cur_list:
            runner = Runner(obj)
            if obj.name != "tests":
                runner.run()
            else:
                m = int((obj.extra.param1 + obj.extra.param2) / 2)
                runner.rps = m
                degr = runner.run()
                if degr:
                    obj.extra.param2 = m
                else:
                    obj.extra.param1 = m
                if obj.extra.param2 == obj.extra.param1 + 1:
                    return left


def arg_parser():
    parser = argparse.ArgumentParser(
        prog='runner',
        description='''This program can start rally tests.''',
        add_help=True
        )
    parser.add_argument(
        '--mock',
        action='store_true',
        default=False,
        help='mock flag'
        )
    sub = parser.add_subparsers(
        dest='action',
        title='mode'
        )
    install_parser = sub.add_parser(
            'install',
            help='install mode'
            )
    run_parser = sub.add_parser(
            'run',
            help='run mode'
            )
    return parser


if __name__ == "__main__":
    parser = arg_parser()
    parse_result = parser.parse_args()
    USER = getpass.getuser()  # current user's username
    PASSWORD = getpass.getpass()  # sudo pasword
    if parse_result.action == "install":
        install_gen = Generator("install")
        for next_list in install_gen:
            for obj in next_list:
                runner = Runner(obj)
                runner.run()
    else:
        run_type = "default"
        if parse_result.mock:
            run_type = "mock"
        run_gen = Generator(run_type)
        for next_list in run_gen:
            n = bin_search(next_list)
            print "="*10
            print "N = %s" % n
            print "="*10
            save_func(n, next_list)

