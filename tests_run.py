#!/usr/bin/env python
import os
import getpass
from sys import argv
from ansible.playbook import PlayBook
from ansible import callbacks
from ansible import utils
from find_n import DegradationCheck
UPPER_BOUND = 200
WEB_SERVERS = ["apache", "uwsgi"]
DBMS = ["postgresql", "mysql"]  # database type
FS = ("/dev/sda7",  # HDD
          "tmpfs",  # overlay
          "/dev/sdb1"  # SSD
          )

OPT = []  # a list of all options
USERNAME = getpass.getuser()  # current user's username
PASSWORD = getpass.getpass()  # sudo pasword


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


def gen_opts():
    test_num = 1
    for run_type in WEB_SERVERS:
        for db in DBMS:
            for fs_src in FS:
                fs_type = "tmpfs" if fs_src == "tmpfs" else "ext4"
                PARAMS = {"global_run_type": run_type,
                          "global_db": db,
                          "global_fs_type": fs_type,
                          "global_fs_src": fs_src,
                          "test_num": str(test_num)
                          }
                OPT.append(PARAMS)
                test_num += 1


def bin_search(params):
    left = 1
    right = UPPER_BOUND
    m = UPPER_BOUND / 2
    while True:
        m = int((left + right) / 2)
        run_playbook("stop_all", params)
        run_playbook("run_dep", params)
        if check_obj.read_json(m):
            right = m
        else:
            left = m
        run_playbook("stop_all", params)
        if right == left + 1:
            return left


if __name__ == "__main__":
    os.chdir("./ansible/")
    gen_opts()
    if len(argv) > 1:
        if argv[1] == "--ignore_install":
            for params in OPT:
                check_obj = DegradationCheck(params)
                N = bin_search(params)
                print("N:", N)
                run_playbook("stop_all", params)
                run_playbook("run_dep", params)
                if not N in check_obj.ID_DICT:
                    check_obj.read_json(N)
                check_obj.save_results(N)
                run_playbook("stop_all", params)
                if N - 1 != 0:
                    run_playbook("stop_all", params)
                    run_playbook("run_dep", params)
                    check_obj.read_json(N - 1)
                    check_obj.save_results(N - 1)
                    run_playbook("stop_all", params)
                for n in (N+1, N+3, N+5, N * 2):
                    run_playbook("stop_all", params)
                    run_playbook("run_dep", params)
                    check_obj.read_json(n)
                    check_obj.save_results(n)
                    run_playbook("stop_all", params)
    else:
        run_playbook("install_all", {})
        """
        for params in OPT:
            check_obj = DegradationCheck(params)
            N = bin_search(params)
            run_playbook("stop_all", params)
            run_playbook("run_dep", params)
            if not N in check_obj.ID_DICT:
                check_obj.read_json(N)
            check_obj.save_results(N)
            run_playbook("stop_all", params)
            if N - 1 != 0:
                run_playbook("stop_all", params)
                run_playbook("run_dep", params)
                check_obj.read_json(N - 1)
                check_obj.save_results(N - 1)
                run_playbook("stop_all", params)
            for n in (N+1, N+3, N+5, N * 2):
                run_playbook("stop_all", params)
                run_playbook("run_dep", params)
                check_obj.read_json(n)
                check_obj.save_results(n)
                run_playbook("stop_all", params)

         """
