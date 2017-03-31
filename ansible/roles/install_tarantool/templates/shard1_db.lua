local uuid4 = require('uuid4')
local sha512 = require('sha512')
local shard = require('shard')

box.cfg{listen = '0.0.0.0:3311'}
--box.cfg{listen = 3311}

box.schema.user.create('lena', {password = 'password', if_not_exists = true})
box.schema.user.grant('lena', 'execute', 'universe', { if_not_exists = true })
box.schema.user.grant('lena', 'read', 'universe', { if_not_exists = true })
box.schema.user.grant('lena', 'write', 'universe', { if_not_exists = true })

local cfg = {
    servers = {

{% for item in range(1, n_slaves|int + 1) %}
    {uri = '{{hostvars[groups[cluster_name + '-slave-%d' | format(item)][0]  ].openstack.private_v4}}:3311', zone = {{'%d'| format(item)}} }, 
{% endfor %}
    }, 
    login = 'lena', 
    password = 'password', 
    redundancy = 1, 
    slab_alloc_arena = 7,
    binary = 3311
}

box.once('create_db', function()

    
    if not box.space.uid_to_uinfo then
        box.schema.space.create('uid_to_uinfo')
        box.space.uid_to_uinfo:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
      --  box.space.uid_to_uinfo:create_index('secondary', {type = 'hash', parts = {2, 'STR'}})
    end

    if not box.space.uname_to_uid then  --new 
        box.schema.space.create('uname_to_uid')
        box.space.uname_to_uid:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
    end

    if not box.space.uid_to_tenants then
        box.schema.space.create('uid_to_tenants')
        box.space.uid_to_tenants:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
    end

    if not box.space.tenid_to_teninfo then
        box.schema.space.create('tenid_to_teninfo')
        box.space.tenid_to_teninfo:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
        --box.space.tenid_to_teninfo:create_index('secondary', {type = 'hash', parts = {2, 'STR'}})
    end

     if not box.space.tenname_to_tenid then --new
        box.schema.space.create('tenname_to_tenid')
        box.space.tenname_to_tenid:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
     end

    if not box.space.tokenid_to_tokeninfo then
        box.schema.space.create('tokenid_to_tokeninfo')
        box.space.tokenid_to_tokeninfo:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
       -- box.space.tokenid_to_tokeninfo:create_index('secondary', {unique = false, parts = {2, 'STR'}})
    end

    -- if not box.space.uid_to_tokenid then --new
     --   box.schema.space.create('uid_to_tokenid')
     --   box.space.uid_to_tokenid:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
    -- end

end)


shard.init(cfg)



