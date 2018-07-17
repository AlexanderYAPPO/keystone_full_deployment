# Keystone_full_deployment project

This project provides scripts for keystone autodeploy in any Openstack\XenServer environment for each of the following configurations:

1. Apache2 + mod_wsgi, Nginx + uwsgi as the HTTP / WSGI frontend, 
2. MariaDB, PostgreSQL as a DBMS 
3. different storage devices: HDD, SSD, TMPFS (instead of a persistent storage device)
4. cassandra ( only for kong keystone plugin)

It includes load generation system (based on the project Rally and gatling) with
automatic critical RPS value search ability

# Dependencies
 ```
 sudo apt-get install libffi-dev libssl-dev python-dev
 pip install --upgrade pip
 pip install --upgrade six ansible shade
 ```
# Configuration
openstack_inventory.py - list of IP addresses by groups (you have to fill this)
ansible/group_vars/all - choose os user name and password

# Installation
Install roles with the install_ * prefix, depending on the required configuration

example:
```
ansible-playbook -i openstack_inventory.py ansible/install_postgresql.yml --extra-vars="ansible_ssh_private_key_file=~/.ssh/my_name_key.key ansible_user=OS_USER cluster_name=my_name_keystone_kong global_database=postgrsql"
```
You can look at all the roles in ansible/roles directory.



# Running

Run keystone-ltest/start_loop_kong.sh (or start_loop.sh or for openstack keystone)
You can change number of kong slaves in the start_loop_kong.sh file.



# Apache Cassandra
Set cassandra_contact_points parameter in roles/install_kong/templates/etc/kong.conf.j2

Tested configurations

Ansible: 2.0.2 and higher.
Python: 2.7.*
Guest OS:
Ubuntu 14.04.1-5

