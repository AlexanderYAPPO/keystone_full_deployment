requirements:

https://github.com/deimosfr/ansible-mariadb/

https://github.com/openstack-ansible-galaxy/openstack-keystone

ansible-mariadb installation task and configuration were changed

Wasn't able to intall from official mariadb repositories

Mariadb didn't start if some are not deleted

## Usage
Keystone can be deployed using Vagrant via included Vagrantfile or on any other machine by running
ansible/deploy_keystone.yml Ansible playbook.

Keystone can be deployed and tests can be started by running
tests_run.py script
If you want to run tests without keystone and rally installation you should use --ignore_install argument
