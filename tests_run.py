import os
import jinja2
import json
import getpass

from sys import argv
from tempfile import NamedTemporaryFile
from ansible.playbook import PlayBook
from ansible import callbacks
from ansible import utils

run_type_opt = ["apache", "uwsgi"]
db_opt = ["mysql", "postgresql"]
fs_opt = ["tmpfs", "/dev/sdb", "dev/sdc"]

OPT = []
os_username = getpass.getuser()
password = getpass.getpass()


def run_playbook(name, extra):
    utils.VERBOSITY = 0
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    stats = callbacks.AggregateStats()
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats,
                                                  verbose=utils.VERBOSITY)

    inventory = """
    [customer]
    {{ public_ip_address }}
    """

    inventory_template = jinja2.Template(inventory)
    rendered_inventory = inventory_template.render({
        'public_ip_address': '127.0.0.1',
    })

    hosts = NamedTemporaryFile(delete=False)
    hosts.write(rendered_inventory)
    hosts.close()

    hosts = NamedTemporaryFile(delete=False)
    hosts.write(rendered_inventory)
    hosts.close()
    pb = PlayBook(
        playbook='/home/%s/keystone_full_deployment/ansible/%s.yml'
                 % (os_username, name),
        host_list=hosts.name,
        remote_user=os_username,
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        private_key_file='/home/%s/.ssh/id_rsa' % os_username,
        become=True,
        become_pass="%s\n" % password,
        become_method='sudo',
        extra_vars=extra
    )
    results = pb.run()
    playbook_cb.on_stats(pb.stats)
    os.remove(hosts.name)
    return results


def get_fs_type(src):
    if "tmpfs":
        return "tmpfs"
    return "ext4"


test_num = 1
for run_type in run_type_opt:
    for db in db_opt:
        for fs_src in fs_opt:
            PARAMS = {"global_run_type": run_type,
                      "global_db": db,
                      "global_fs_type": get_fs_type(fs_src),
                      "global_fs_src": fs_src,
                      "test_num": str(test_num)
                      }
            params_s = json.dumps(PARAMS)
            OPT.append(PARAMS)
            test_num += 1


def install():
    run_playbook("install_all", {})


def stop(params):
    run_playbook("stop_all", params)


def run_deps():
    for params in OPT:
        stop(params)
        run_playbook("run_dep", params)
        run_playbook("run_tests", params)
        stop(params)


os.chdir("./ansible/")
if sys.argv[1] != "--ignore_install"
    install()
run_deps()

