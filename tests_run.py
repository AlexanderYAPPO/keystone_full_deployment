import os
import jinja2
import getpass

from sys import argv
from tempfile import NamedTemporaryFile
from ansible.playbook import PlayBook
from ansible import callbacks
from ansible import utils

WEB_SERVERS = ["apache", "uwsgi"]
DBMS = ["mysql", "postgresql"]  # database type
FS = ("tmpfs",
          "/dev/sdb",  # device name
          "/dev/sdc"  # SSD can be used
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


def run_deps():
    for params in OPT:
        run_playbook("stop_all", params)
        run_playbook("run_dep", params)
        run_playbook("run_tests", params)
        run_playbook("stop_all", params)


if __name__ == "__main__":
    os.chdir("./ansible/")
    gen_opts()
    if len(argv) > 1:
        if argv[1] == "--ignore_install":
            run_deps()
    else:
        run_playbook("install_all", {})
        run_deps()

