#!/bin/bash
sbt assembly
#for i in `seq 29 32`;
typeset -a errors=(29 30 31 32)
for i in "${errors[@]}"
do
    echo Number of vms: $i
    prev_nodes_numb=$(( $i - 1 ))
    first_line=$(head -n 1 /home/ubuntu/gatling_volume_2/gatling_ouptut/360sec_keystone/keystone_$prev_nodes_numb/results)
    fl_len=${#first_line}
    if [ "$fl_len" -eq "0" ]; then  first_line=10; fi
    min=$(( ($first_line +60)/2))
    echo minRPS: $min
    source /home/ubuntu/sandbox-openrc.sh
    ansible-playbook -c paramiko -i /home/ubuntu/keystone_full_deployment/ansible/openstack_inventory.py /home/ubuntu/keystone_full_deployment/ansible/run_haproxy.yml --extra-vars="timeout=600 ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=ubuntu cluster_name=my_name_keystone global_database=postgresql n_slaves=$i"
    /home/ubuntu/keystone_full_deployment/ansible/runner.py -uubuntu -pNONE run
    source /home/ubuntu/ral.sh
    java -cp target/scala-2.11/keystone-ltest-assembly-1.0.jar keystone_ltest.bsearch.BSearch "$@" --rounds 1 --minRps $min --duration 360 --out-dir /home/ubuntu/gatling_volume_2/gatling_ouptut/360sec_keystone/keystone_$i
    ./tgm.py
done

