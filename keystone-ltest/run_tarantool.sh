#!/bin/bash
#sbt assembly
#for i in `seq 15 32`;
#do
#    echo Number of vms: $i
#    prev_nodes_numb=$(( $i - 1 ))
#    fist_line=$(head -n 1 /home/ubuntu/gatling_volume/gatling_ouptut/10sec/tarantool_$prev_nodes_numb/results)
#    fl_len=${#fist_line}
#    if [ "$fl_len" -eq "0" ]; then   fist_line=800; fi
#    source /home/ubuntu/sandbox-openrc.sh 
#    ansible-playbook -i /home/ubuntu/keystone_full_deployment/ansible/openstack_inventory.py /home/ubuntu/keystone_full_deployment/ansible/install_tarantool.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=ubuntu cluster_name=my_name_keystone global_database=postgresql n_slaves=$i"

#    ansible-playbook -i /home/ubuntu/keystone_full_deployment/ansible/openstack_inventory.py /home/ubuntu/keystone_full_deployment/ansible/run_haproxy_tarantool.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=ubuntu cluster_name=my_name_keystone global_database=postgresql n_slaves=$i"

#    /home/ubuntu/keystone_full_deployment/ansible/runner_tarantool.py -uubuntu -pNONE run
#    source /home/ubuntu/ral.sh
#    java -cp target/scala-2.11/keystone-ltest-assembly-1.0.jar keystone_ltest.bsearch.BSearch "$@" --minRps $fist_line --duration 10 --out-dir /home/ubuntu/gatling_volume/gatling_ouptut/10sec/tarantool_$i
#done 


#for i in `seq 27 27`;
#errors[0] = 15
#errors[1] = 20
#errors[2] = 21
#(15, 20, 21, 22, 24, 30, 31)
typeset -a errors=(31)
for i in "${errors[@]}" 
do
    echo Number of vms: $i
    prev_nodes_numb=$(( $i - 1 ))
    first_line=$(head -n 1 /home/ubuntu/gatling_volume/gatling_ouptut/360sec/tarantool_$prev_nodes_numb/results)
    fl_len=${#first_line}
    if [ "$fl_len" -eq "0" ]; then  first_line=1851; fi
    min=$(( ($first_line +100)/2 ))
    echo minRPS: $min
    source /home/ubuntu/sandbox-openrc.sh 
    ansible-playbook -c paramiko -i /home/ubuntu/keystone_full_deployment/ansible/openstack_inventory.py /home/ubuntu/keystone_full_deployment/ansible/install_tarantool.yml --extra-vars="timeout=600 ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=ubuntu cluster_name=my_name_keystone global_database=postgresql n_slaves=$i"

    ansible-playbook -c paramiko -i /home/ubuntu/keystone_full_deployment/ansible/openstack_inventory.py /home/ubuntu/keystone_full_deployment/ansible/run_haproxy_tarantool.yml --extra-vars="timeout=600 ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=ubuntu cluster_name=my_name_keystone global_database=postgresql n_slaves=$i"

    /home/ubuntu/keystone_full_deployment/ansible/runner_tarantool.py -uubuntu -pNONE run
    source /home/ubuntu/ral.sh
    java -cp target/scala-2.11/keystone-ltest-assembly-1.0.jar keystone_ltest.bsearch.BSearch "$@" --rounds 3 --minRps $min --duration 360 --out-dir /home/ubuntu/gatling_volume_2/gatling_ouptut/360sec/tarantool_$i
done 

#for i in `seq 1 32`;
#do
#    echo Number of vms: $i
#    source /home/ubuntu/sandbox-openrc.sh 
#    ansible-playbook -i /home/ubuntu/keystone_full_deployment/ansible/openstack_inventory.py /home/ubuntu/keystone_full_deployment/ansible/run_haproxy.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=ubuntu cluster_name=my_name_keystone global_database=postgresql n_slaves=$i"

#    /home/ubuntu/keystone_full_deployment/ansible/runner.py -uubuntu -pNONE run
#    source /home/ubuntu/ral.sh
#    java -cp target/scala-2.11/keystone-ltest-assembly-1.0.jar keystone_ltest.bsearch.BSearch "$@" --minRps 10 --rounds 1 --duration 10 --out-dir /home/ubuntu/gatling_volume/gatling_ouptut/10sec_keystone/keystone_$i
#done 

#for i in `seq 1 32`;
#do
#    echo Number of vms: $i
#    source /home/ubuntu/sandbox-openrc.sh 
#    ansible-playbook -i /home/ubuntu/keystone_full_deployment/ansible/openstack_inventory.py /home/ubuntu/keystone_full_deployment/ansible/run_haproxy.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=ubuntu cluster_name=my_name_keystone global_database=postgresql n_slaves=$i"

#    /home/ubuntu/keystone_full_deployment/ansible/runner.py -uubuntu -pNONE run
#    source /home/ubuntu/ral.sh
#    java -cp target/scala-2.11/keystone-ltest-assembly-1.0.jar keystone_ltest.bsearch.BSearch "$@" --minRps 10 --rounds 3 --duration 360 --out-dir /home/ubuntu/gatling_volume/gatling_ouptut/360sec_keystone/keystone_$i
#done 
