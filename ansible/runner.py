#!/usr/bin/python
from argparse import ArgumentParser
#from ansible.playbook import PlayBook
#from ansible import callbacks
#from ansible import utils
from degr_kong import DegradationCheck
from getpass import getuser
import os
import sys
from collections import namedtuple

from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor
inventory = None
variable_manager = None
WEB_SERVERS = ["uwsgi"]
BACKENDS = ["postgresql"]  # database type
HARDWARE_LIST = (
    #"HDD",
    #"/dev/sdb1",  # SSD
    "tmpfs",  # overlay
    #"/dev/sda7"  # HDD
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
                Task("install", "postgresql", Extra()),
                #Task("install", "mysql", Extra()),
                Task("install", "keystone", Extra()),
                #Task("install", "apache", Extra()),
                Task("install", "uwsgi", Extra()),
                #Task("install", "rally", Extra()),
                #Task("install", "mock", Extra())
                ]
            self.gen_list.append(new_list)

        elif act == "default":
            for database in BACKENDS:
                for web_server in WEB_SERVERS:
                    for hardware in HARDWARE_LIST:
                        new_list = [
                            Task("stop", "kong", Extra()),
             
                            Task("stop", "uwsgi", Extra()),
                            Task("stop", "redis", Extra()),
                            Task("stop", "postgresql", Extra()),
                            Task("stop", "cassandra", Extra()),
                            Task("umount", hardware, Extra(database)),
                            #Task("mount", hardware, Extra(database)),
                            Task("stop", "postgresql", Extra()),
                            Task("run", "cassandra", Extra()),
                            Task("run", "kong", Extra()),
                            #Task("stop", "tarantool", Extra()),
                            #Task("stop", "rally", Extra()),
                            #Task("run_instances", web_server, Extra()),
                            #Task("stop", web_server, Extra()),
                            #Task("stop", database, Extra()),
                            #Task("stop", "apache", Extra()),
                            #Task("umount", "mysql", Extra()),
                            #Task("umount", "postgresql", Extra()),
                            #Task("umount", "postgresql", Extra(database)),
                            #Task("mount", hardware, Extra(database)),
                            #Task("install", "postgresql", Extra()),
                            #Task("install", "uwsgi", Extra()),
                            #Task("install", "keystone", Extra()),
                            #Task("run", database, Extra(database)),

                            #Task("run", web_server, Extra(database)),
                            #Task("run", "inittarantool", Extra(database)),
                            ##Task("func", "tests", Extra(database,
                            ##                            hardware,
                            ##                           web_server,
                            ##                           1,
                            ##                            500
                            ##                            )),
                            ###Task("stop", web_server, Extra()),
                            ##Task("stop", database, Extra()),
                            #T#ask("umount", database, Extra(database))
#                           # Task("stop", "rally", Extra())
                            ]
                        self.gen_list.append(new_list)

        elif act == "mock":
            new_list = [
                Task("run", "mock", Extra()),
                Task("func", "tests", Extra("flask",
                                            "flask",
                                            "flask",
                                            199,
                                            1200,
                                            )),
                Task("stop", "mock", Extra()),
                #Task("stop", "rally", Extra())
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
    @staticmethod
    def run(task, rps=0):
        action = task.action
        name = task.name
        extra = task.extra
        if action == "mount" or action == "umount":
            f_system = "tmpfs" if name == "tmpfs" else "ext4"
            Runner.run_playbook("%s_%s" % (action, extra.database),
                hardware_src=name,
                hardware_type=f_system
                )
        elif action == "stop" or action == "install":
            if name == "rally":
                Runner.run_playbook("%s_%s" % (action, name),
                                    global_os_user=getuser())
            else:
                Runner.run_playbook("%s_%s" % (action, name))

        elif action == "run":
            if name in WEB_SERVERS:
                Runner.run_playbook("%s_%s" % (action, name),
                                    global_db=extra.database)
            else:
                Runner.run_playbook("%s_%s" % (action, name))
        elif action == "func":
            if name == "tests":
                d = DegradationCheck(extra.hardware, extra.database,
                                     extra.web_server)
                isdeg = d.is_degradation(rps)
                d.save_results(rps)
                return isdeg#d.is_degradation(rps)
            elif name == "save":
                d = DegradationCheck(extra.hardware, extra.database,
                                     extra.web_server)
                d.is_degradation(rps)
                d.save_results(rps)

    @staticmethod
    def run_playbook(name, **kwargs):
        kwargs["cluster_name"] = "my_name_keystone_kong"
        with open("/home/modis/cur_n.txt", "r") as f:
            txt = f.readline()
        print(txt)
        kwargs["n_slaves"] = txt.replace("\n", "")
        #kwargs["global_db"] = "postgresql"
        kwargs["ansible_ssh_private_key_file"] = "~/.ssh/my_name_key.key"
        ansible_dir = "/home/%s/keystone_full_deployment/ansible" % getuser()

        loader = DataLoader()
        global variable_manager
        global inventory
        if inventory is None:
            variable_manager = VariableManager()
            inventory = Inventory(loader=loader, variable_manager=variable_manager,  host_list="%s/openstack_inventory.py" % ansible_dir)
            variable_manager.set_inventory(inventory)
        playbook_path = '/home/%s/keystone_full_deployment/ansible/%s.yml' % (getuser(), name)
        if not os.path.exists(playbook_path):
            print '[INFO] The playbook does not exist'
            sys.exit()

        Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path', 'forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])
        options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, forks=100, remote_user=_user, private_key_file='/home/%s/.ssh/id_rsa' % getuser(), ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True, become_method="sudo", become_user="root", verbosity=None, check=False)

        variable_manager.extra_vars = kwargs # This can accomodate various other command line arguments.`

        passwords = dict(vault_pass="%s\n" % _password, sudo_pass="%s\n" % _password, become_pass="%s\n" % _password)
        pbex = PlaybookExecutor(playbooks=[playbook_path], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=passwords)
        results = pbex.run()

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


def save_n(cnf, n):
    results_dir = "/home/%s/results/%s/%s/%s" % (
                                                getuser(),
                                                cnf.hardware.replace("/", ""),
                                                cnf.database,
                                                cnf.web_server
                                                )
    with open(results_dir + '/N=%s' % n, 'w') as f:
        f.write("N=%s\n" % (n))

def save_func(n, cur_config):
    for rps in (n, n-1, n-2, n-3 , n+1, n+3):#, n-1, n-2, n+1, n+3):#for rps in (n, n - 1, n-2, n + 1, n + 3, n + 5, 2 * n):
        for obj in cur_config:
            if obj.name == "tests":
                Runner.run(Task("func", "save", obj.extra), rps)
                if rps == n:
                    save_n(obj.extra, n)
            else:
                Runner.run(obj)

def save_without_run(n, cur_config):
    for obj in cur_config:
        if obj.name == "tests":
            save_n(obj.extra, n)

def bin_search(cur_config):
    result = 0
    while not result:
        for obj in cur_config:
            if obj.name == "tests":
                m = int((obj.extra.param1 + obj.extra.param2) / 2)
                degr = Runner.run(obj, m)
                if degr:
                    obj.extra.param2 = m
                else:
                    obj.extra.param1 = m
                if obj.extra.param2 <= obj.extra.param1 + 1:
                    result = obj.extra.param1
            else:
                Runner.run(obj)
    return result



def main():
    if _parse_result.action == "install":
        install_gen = Generator("install")
        for next_list in install_gen:
            for obj in next_list:
                Runner.run(obj)
    elif _parse_result.action == "run":
        run_type = "default"
        if _parse_result.mock:
            run_type = "mock"
        run_gen = Generator(run_type)
        #"""
        next_config = run_gen.next()
        n = 500
        for obj in next_config:
            if obj.name == "tests":
                Runner.run(Task("func", "save", obj.extra), n)
                save_n(obj.extra, n)
            else:
                Runner.run(obj)
        """
        for next_list in run_gen:
            n = bin_search(next_list)
            print "="*10
            print "N = %s" % n
            print "="*10
            #save_func(n, next_list)
            save_without_run(n, next_list)
        """
if __name__ == "__main__":
    _parser = arg_parser()
    _parse_result = _parser.parse_args()
    _password = _parse_result.password
    _user = _parse_result.user
    print _user, _password
    try:
        main()
    except KeyboardInterrupt:
        print "\n"+"="*10
        print "interrupted"
        print "="*10
        for service in BACKENDS + WEB_SERVERS:
            Runner().run(Task("stop", service, Extra()))


