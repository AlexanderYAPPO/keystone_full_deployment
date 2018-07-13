#!/bin/bash
#export SBT_OPTS="-Xmx40G -XX:+UseConcMarkSweepGC -XX:+CMSClassUnloadingEnabled -XX:MaxPermSize=40G -Xss10M  -Duser.timezone=GMT"
sbt assembly
typeset -a errors=( 9 1 8 7 6 5 4 3 2 1 11 12) #1 11 8 7 6 5 4 3 2 12 )
#source /home/modis/openrc.sh
source /home/modis/export_env.sh
#for (( n_slaves = 9; n_slaves <= 9; n_slaves++ ))
for n_slaves in "${errors[@]}"
do
killall /usr/bin/python
#    sbt assembly
    echo $n_slaves > /home/modis/cur_n.txt
    ansible-playbook -i /home/modis/keystone_full_deployment/ansible/openstack_inventory.py /home/modis/keystone_full_deployment/ansible/stop_memcache.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=modis cluster_name=my_name_keystone_kong global_database=postgrsql n_slaves=$n_slaves"
    ansible-playbook -i /home/modis/keystone_full_deployment/ansible/openstack_inventory.py /home/modis/keystone_full_deployment/ansible/run_haproxy.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=modis cluster_name=my_name_keystone_kong global_database=postgrsql n_slaves=$n_slaves"
    #/home/modis/keystone_full_deployment/ansible/runner.py -u modis -p PASSWORDun
    java -cp target/scala-2.11/keystone-ltest-assembly-1.0.jar keystone_ltest.bsearch.BSearch "$@" --minRps 1000 --rounds 1 --duration 180 --out-dir /home/modis/results/gatling_output/keystone/$n_slaves
    ansible-playbook -i /home/modis/keystone_full_deployment/ansible/openstack_inventory.py /home/modis/keystone_full_deployment/ansible/stop_memcache.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=modis cluster_name=my_name_keystone_kong global_database=postgrsql n_slaves=$n_slaves"
done
