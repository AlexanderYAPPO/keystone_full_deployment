#!/bin/bash
export SBT_OPTS="-Xmx8192M -XX:+UseConcMarkSweepGC -XX:+CMSClassUnloadingEnabled  -Xss20M  -Duser.timezone=GMT -Xmx8192M"
sbt assembly
typeset -a errors=(1 3 9 2 4 5 6 7 8)
#typeset -a errors=(1)
#source /home/modis/openrc.sh
source /home/modis/export_env.sh
#for (( n_slaves = 9; n_slaves <= 9; n_slaves++ ))
for n_slaves in "${errors[@]}"
do
    echo $n_slaves > /home/modis/cur_n.txt
    killall /usr/bin/python
#    sbt assembly
    #echo $n_slaves > /home/modis/keystone_full_deployment/ansible/current_num_of_slaves.txt
    #ansible-playbook -i /home/modis/keystone_full_deployment/ansible/openstack_inventory.py /home/modis/keystone_full_deployment/ansible/stop_memcache.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=modis cluster_name=my_name_keystone_kong global_database=postgrsql n_slaves=$n_slaves"
    ansible-playbook -i /home/modis/keystone_full_deployment/ansible/openstack_inventory.py /home/modis/keystone_full_deployment/ansible/run_haproxy_kong.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=modis cluster_name=my_name_keystone_kong global_database=postgrsql n_slaves=$n_slaves"
    #/home/modis/keystone_full_deployment/ansible/runner_kong.py -u modis -p PASSWORDun

    #ansible-playbook -i /home/modis/keystone_full_deployment/ansible/openstack_inventory.py /home/modis/keystone_full_deployment/ansible/run_kong.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=modis cluster_name=my_name_keystone_kong global_database=postgrsql n_slaves=$n_slaves"
    java -cp target/scala-2.11/keystone-ltest-assembly-1.0.jar keystone_ltest.bsearch.BSearch "$@" --minRps 1000 --rounds 1 --duration 90 --out-dir /home/modis/results/gatling_output/keystone/$n_slaves
done
