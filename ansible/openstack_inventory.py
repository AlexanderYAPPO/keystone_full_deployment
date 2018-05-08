[bogomolov_keystone-rally]
172.31.4.102
[bogomolov_keystone-HAProxy]
172.31.231.65
[bogomolov_keystone_kong-cache]
172.31.51.158
[bogomolov_keystone_kong-slave-1]
172.31.14.36
[bogomolov_keystone_kong-slave-2]
172.31.123.183
[bogomolov_keystone_kong-slave-3]
172.31.186.226
[bogomolov_keystone_kong-slave-4]
172.31.159.232
[bogomolov_keystone_kong-slave-5]
172.31.161.118
[bogomolov_keystone_kong-slave-6]
172.31.116.102
[bogomolov_keystone_kong-slave-7]
172.31.161.142
[bogomolov_keystone_kong-slave-8]
172.31.210.166
[bogomolov_keystone_kong-slave-9]
172.31.45.40
[bogomolov_keystone_kong_slaves]
172.31.14.36      real_hostname=ub16    # kong 1
172.31.123.183      real_hostname=ub17  # kong 2
172.31.186.226      real_hostname=ub18  # kong 3
172.31.159.232      real_hostname=ub19  # kong 4
172.31.161.118      real_hostname=ub20  # kong 5
172.31.116.102      real_hostname=ub21  # kong 6
172.31.161.142      real_hostname=ub22  # kong 7
172.31.210.166      real_hostname=ub23  # kong 8
172.31.45.40      real_hostname=ub24    # kong 9
#172.31.175.193      real_hostname=ub25   # cassandra 4 \ postgresql 



[bogomolov-cassandra-master]
172.31.110.38
#172.31.44.237

[bogomolov-cassandra-slaves]
172.31.125.109
172.31.149.109
#####172.31.181.242  # 4
#####172.31.175.193  # 5
#172.31.120.175
#172.31.130.41
#172.31.115.114
#172.31.125.109
#172.31.86.201
#172.31.7.177
#172.31.243.143
#172.31.80.96
#172.31.12.159
#172.31.109.115
#172.31.68.165

[bogomolov-cassandra-slave-1]
172.31.125.109
#172.31.120.175
[bogomolov-cassandra-slave-2]
172.31.149.109
#172.31.130.41
[bogomolov-cassandra-slave-3]
172.31.181.242
#172.31.115.114
[bogomolov-cassandra-slave-4]
172.31.175.193
#172.31.125.109
#[bogomolov-cassandra-slave-5]
#172.31.86.201
#[bogomolov-cassandra-slave-6]
#172.31.7.177
#[bogomolov-cassandra-slave-7]
#172.31.243.143
#[bogomolov-cassandra-slave-8]
#172.31.80.96
#[bogomolov-cassandra-slave-9]
#172.31.12.159
#[bogomolov-cassandra-slave-10]
#172.31.109.115
#[bogomolov-cassandra-slave-11]
#172.31.68.165

[xenvirts]
#172.31.4.102      real_hostname=ub13    # bogomolov_keystone-rally 
172.31.231.65      real_hostname=ub14   # HAproxy
172.31.51.158      real_hostname=ub15   # memcache
172.31.14.36      real_hostname=ub16    # kong 1
172.31.123.183      real_hostname=ub17  # kong 2
172.31.186.226      real_hostname=ub18  # kong 3
172.31.159.232      real_hostname=ub19  # kong 4
172.31.161.118      real_hostname=ub20  # kong 5
172.31.116.102      real_hostname=ub21  # kong 6
172.31.161.142      real_hostname=ub22  # kong 7
172.31.210.166      real_hostname=ub23  # kong 8
172.31.45.40      real_hostname=ub24    # kong 9
172.31.175.193      real_hostname=ub25   # cassandra 4 \ postgresql 
172.31.181.242      real_hostname=ub26   # cassandra 3  !
172.31.149.109      real_hostname=ub27   # cassandra 2 
172.31.125.109      real_hostname=ub28   # cassandra 1  !
172.31.110.38      real_hostname=ub29    # cassandra "master"
#172.31.44.237      real_hostname=cashdd00
#172.31.120.175      real_hostname=cashdd1
#172.31.130.41      real_hostname=cashdd2
#172.31.115.114      real_hostname=cashdd3
#172.31.125.109      real_hostname=cashdd4
#172.31.86.201      real_hostname=cashdd5
#172.31.7.177      real_hostname=cashdd6
#172.31.243.143      real_hostname=cashdd7
#172.31.80.96      real_hostname=cashdd8
#172.31.12.159      real_hostname=cashdd9
#172.31.109.115      real_hostname=cashdd10
#172.31.68.165      real_hostname=cashdd11
[xenvirts:vars]
ansible_user=modis
ansible_sudo_password="***REMOVED***"
host_key_checking = False
