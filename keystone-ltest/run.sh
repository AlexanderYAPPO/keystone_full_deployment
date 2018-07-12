#!/bin/bash
sbt assembly
source /home/ubuntu/sandbox-openrc.sh 


for i in `seq 1 32`;
do
    echo Number of vms: $i
    ansible-playbook -i /home/ubuntu/keystone_full_deployment/ansible/openstack_inventory.py /home/ubuntu/keystone_full_deployment/ansible/run_haproxy_tarantool.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/myname_key.key ansible_user=ubuntu cluster_name=myname_keystone global_database=mysql n_slaves=$i"
    ansible-playbook -i /home/ubuntu/keystone_full_deployment/ansible/openstack_inventory.py /home/ubuntu/keystone_full_deployment/ansible/install_tarantool.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/myname_key.key ansible_user=ubuntu cluster_name=myname_keystone global_database=postgresql n_slaves=$i"
    /home/ubuntu/keystone_full_deployment/ansible/runner_tarantool.py -uubuntu -pNONE run
	java -cp target/scala-2.11/keystone-ltest-assembly-1.0.jar keystone_ltest.bsearch.BSearch "$@" --minRps 1 --duration 10 --out-dir ~/home/ubuntu/gatling_volume/gatling_ouptut/10sec/tarantool_$i
done    

