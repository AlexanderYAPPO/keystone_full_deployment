# ansible-role-kong

**This role is not longer maintained here. Please checkout [Mashape's fork](https://github.com/Mashape/ansible-role-kong)**

[![Ansible Galaxy](http://img.shields.io/badge/ansible--galaxy-jessem.kong-blue.svg)](https://galaxy.ansible.com/detail#/role/7032) [![Build Status](https://travis-ci.org/Getsidecar/ansible-role-kong.svg?branch=master)](https://travis-ci.org/Getsidecar/ansible-role-kong)

An Ansible role that installs [Kong](https://getkong.org) on Ubuntu.  

## Requirements

Kong uses [Cassandra](https://cassandra.apache.org/) as its data store, however this role does not include it. See `kong_conf_databases_available` for configuring your Cassandra instance with Kong.   

## Role Variables

Default configuration is defined in [default vars](defaults/main.yml).

This role downloads the Kong source directly from [the GitHub repo](https://github.com/Mashape/kong/releases) which offers multiple flavors of Ubuntu.    

## Dependencies

None

## Example Playbook

    - hosts: kong_servers
      roles:
        - { role: ansible-role-kong }

## License

See the LICENSE file for license rights and limitations (MIT).
