#!/usr/bin/env python
from argparse import ArgumentParser
from ansible.playbook import PlayBook
from ansible import callbacks
from ansible import utils
from degr import DegradationCheck

WEB_SERVERS = ["apache", "uwsgi"]
BACKENDS = ["postgresql", "mysql"]  # database type
HARDWARE_LIST = (
    "/dev/sda7",  # HDD
    "tmpfs",  # overlay
    "/dev/sdb1"  # SSD
    )


class Extra():
    def __init__(self, database=None, hardware=None,
                 web_server=None, param1=None, param2=None):
        self.database = database
        self.web_server = web_server
        self.hardware = hardware
        self.param1 = param1
        self.param2 = param2


class Task:
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
                Task("install", "tests", Extra()),
                Task("install", "postgresql", Extra()),
                Task("install", "mysql", Extra()),
                Task("install", "keystone", Extra()),
                Task("install", "apache", Extra()),
                Task("install", "uwsgi", Extra()),
                Task("install", "rally", Extra()),
                Task("install", "mock", Extra())
                ]
            self.gen_list.append(new_list)

        elif act == "default":
            for database in BACKENDS:
                for web_server in WEB_SERVERS:
                    for hardware in HARDWARE_LIST:
                        new_list = [
                            #Task("stop", database, Extra()),
                            #Task("stop", web_server, Extra()),
                            Task("mount", hardware, Extra(database)),
                            Task("run", database, Extra(database)),
                            Task("run", web_server, Extra(database)),
                            Task("func", "tests", Extra(database,
                                                        hardware,
                                                        web_server,
                                                        1,
                                                        200
                                                        )),
                            Task("stop", web_server, Extra()),
                            Task("stop", database, Extra()),
                            Task("umount", database, Extra(database)),
                            Task("stop", "rally", Extra())
                            ]
                        self.gen_list.append(new_list)

        elif act == "mock":
            new_list = [
                Task("run", "mock", Extra()),
                Task("func", "tests", Extra("flask",
                                            "flask",
                                            "flask",
                                            500,
                                            1000
                                            )),
                Task("stop", "mock", Extra()),
                Task("stop", "rally", Extra())
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

def run_playbook(name, **kwargs):
    utils.VERBOSITY = 0
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    stats = callbacks.AggregateStats()
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats,
                                                  verbose=utils.VERBOSITY)
    ansible_dir = "/home/%s/keystone_full_deployment/ansible" % _user
    pb = PlayBook(
        playbook='%s/%s.yml' % (ansible_dir, name),
        host_list="%s/hosts" % ansible_dir,
        remote_user=_user,
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        private_key_file='/home/%s/.ssh/id_rsa' % _user,
        become=True,
        become_pass="%s\n" % _password,
        become_method='sudo',
        extra_vars=kwargs
    )
    results = pb.run()
    playbook_cb.on_stats(pb.stats)
    return results

class Runner:
    @staticmethod
    def run(task, rps=0):
        action = task.action
        name = task.name
        extra = task.extra
        if action == "mount" or action == "umount":
            hardware_type = "tmpfs" if name == "tmpfs" else "ext4"
            run_playbook("%s_%s" % (action, extra.database),
                hardware_src="name",
                hardware_type="hardware_type"
                )
        elif action == "stop" or action == "install":
            run_playbook("%s_%s" % (action, name))
        elif action == "run":
            if name in WEB_SERVERS:
                run_playbook("%s_%s" % (action, name), 
                                    global_database=extra.database)
            else:
                run_playbook("%s_%s" % (action, name))
        elif action == "func":
            if name == "tests":
                d = DegradationCheck(extra.hardware, extra.database,
                                     extra.web_server, _user)
                return d.is_degradation(rps)
            elif name == "save":
                d = DegradationCheck(extra.hardware, extra.database,
                                     extra.web_server, _user)
                d.is_degradation(rps)
                d.save_results(rps)


def arg_parser():
    parser = ArgumentParser(
        prog = 'runner',
        description = '''This program can start rally tests.''',
        add_help = True
        )
    parser.add_argument ('--user',
        "-u",
        action="store",
        default="",
        help="sudo user",
        required=True
        )
    parser.add_argument ('--password',
        "-p", 
        action="store",
        default="",
        help="sudo password",
        required=True
        )
    sub = parser.add_subparsers (dest = 'action',
        title = 'mode'
        )
    install_parser = sub.add_parser ('install',
        help = 'install mode')
    run_parser = sub.add_parser ('run',
        help = 'run mode')
    run_parser.add_argument ('--mock', action='store_true',
        default = False,
        help = 'mock flag')
    return parser


def save_func(n, cur_config):
    for rps in (n - 1, n, n + 1, n + 3, n + 5, 2 * n):
        for obj in cur_config:
            if obj.name == "tests":
                Runner.run(Task("func", "save", obj.extra))
            Runner.run(Task("func", "save", obj.extra))


def bin_search(cur_config):
    result = 0
    while not result:
        for obj in cur_config:
            if obj.name == "tests":
                m = int((obj.extra.param1 + obj.extra.param2) / 2)
                degr = Runner.run(obj, rps)
                if degr:
                    obj.extra.param2 = m
                else:
                    obj.extra.param1 = m
                if obj.extra.param2 == obj.extra.param1 + 1:
                    result = obj.extra.param1
            else:
                Runner.run(obj)
    return result
    


def main():
    if _parse_result.action == "install":
        install_gen = Generator("install")
        for next_list in install_gen:
            for obj in next_list:
                runner = Runner()
                runner.run(obj)
    elif _parse_result.action == "run":
        run_type = "default"
        if _parse_result.mock:
            run_type = "mock"
        run_gen = Generator(run_type)
        for next_list in run_gen:
            n = bin_search(next_list)
            print "="*10
            print "N = %s" % n
            print "="*10
            save_func(n, next_list)


if __name__ == "__main__":
    _parser = arg_parser()
    _parse_result = _parser.parse_args()
    _user = _parse_result.user
    _password = _parse_result.password
    print _user, _password
    try:
        main()
    except KeyboardInterrupt:
        print "\n"+"="*10
        print "interrupted"
        print "="*10
        for service in BACKENDS + WEB_SERVERS:
            Runner().run(Task("stop", service, Extra()))

