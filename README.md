requirements:

ansible==1.9.3

https://github.com/deimosfr/ansible-mariadb/

https://github.com/openstack-ansible-galaxy/openstack-keystone

ansible-mariadb installation task and configuration were changed

Wasn't able to install from official mariadb repositories

Mariadb didn't start if some are not deleted

## Usage

usage: runner [-h] --user USER -password PASSWORD {install, run} [--mock]

--mock if set true the mock will be used instead of keystone
