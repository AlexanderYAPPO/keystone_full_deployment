import os
import jinja2
import json
import getpass

from tempfile import NamedTemporaryFile
from ansible.playbook import PlayBook
from ansible.inventory import Inventory
from ansible import callbacks
from ansible import utils

run_type_opt = ["apache", "uwsgi"]
db_opt = ["mysql", "postgresql"]
fs_opt = ["tmpfs", "/dev/sdb", "dev/sdc"]

OPT = []
password = getpass.getpass()

def run_playbook(name, extra):

    utils.VERBOSITY = 0
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    stats = callbacks.AggregateStats()
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

    inventory = """
    [customer]
    {{ public_ip_address }}

    [customer:vars]
    domain={{ domain_name }}
    customer_id={{ customer_id }}
    customer_name={{ customer_name }}
    customer_email={{ customer_email }}
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
        playbook='/home/ubuntu/keystone_full_deployment/ansible/%s.yml'% name,
        host_list=hosts.name,  
        remote_user='ubuntu',
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        private_key_file='/home/ubuntu/.ssh/id_rsa',
        become=True, 
        become_pass = "%s\n" % password,
        become_method = 'sudo',
        extra_vars = extra
    
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
            PARAMS = {"global_run_type" : run_type,
                      "global_db" : db,
                      "global_fs_type" : get_fs_type(fs_src),
                      "global_fs_src" : fs_src,
                      "test_num" : str(test_num)
                      }
            params_s = json.dumps(PARAMS)
            OPT.append(PARAMS)
            test_num += 1

def install():
    sh_text = "ansible-playbook -i hosts -K install_all.yml"
    run_playbook("install_all", {})

def stop(params):
    sh_text = "ansible-playbook -i hosts -K stop_all.yml --extra-vars '%s'" % params
    run_playbook("stop_all",params)

def run_deps():
    for params in OPT:
        stop(params)
        sh_text = "ansible-playbook -i hosts -K run_dep.yml --extra-vars '%s'" % params
        run_playbook("run_dep", params)
        test_sh = "ansible-playbook -i hosts -K run_tests.yml --extra-vars '%s'" % params
        run_playbook("run_tests", params)
        stop(params)

os.chdir("./ansible/")
#install()
run_deps()
