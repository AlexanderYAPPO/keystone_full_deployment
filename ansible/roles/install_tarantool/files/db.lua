local uuid4 = require('uuid4')
local sha512 = require('sha512')

box.cfg{
		listen = '0.0.0.0:3303',
		replication_source = {
{% for item in range(1, n_slaves|int + 1) %}
    "replicator:password@{{hostvars[groups[cluster_name + '-slave-%d' | format(item)][0]  ].openstack.private_v4}}:3303",
{% endfor %}
                             }
        }
box.once('create_users', function()
			box.schema.user.create('lena', {password = 'password', if_not_exists = true})
			box.schema.user.grant('lena', 'execute', 'universe', { if_not_exists = true })
			box.schema.user.grant('lena', 'read', 'universe', { if_not_exists = true })
			box.schema.user.grant('lena', 'write', 'universe', { if_not_exists = true })

			box.schema.user.create('replicator', {password = 'password', if_not_exists = true})
			box.schema.user.grant('replicator', 'execute', 'role', 'replication', 
			{ if_not_exists = true })
		end)
--box.schema._cluster:select({0}, {iterator = 'GE'})

box.once('create_db_tester', function()

        if not box.space.uid_to_uinfo then
            box.schema.space.create('uid_to_uinfo')
            box.space.uid_to_uinfo:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
          --  box.space.uid_to_uinfo:create_index('secondary', {type = 'hash', parts = {2, 'STR'}})
        end
        
        if not box.space.uname_to_uid then  --new 
            box.schema.space.create('uname_to_uid')
            box.space.uid_to_uinfo:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
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
            box.space.tenid_to_teninfo:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
         end

        if not box.space.tokenid_to_tokeninfo then
            box.schema.space.create('tokenid_to_tokeninfo')
            box.space.tokenid_to_tokeninfo:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
           -- box.space.tokenid_to_tokeninfo:create_index('secondary', {unique = false, parts = {2, 'STR'}})
        end
        
         if not box.space.uid_to_tokenid then --new
            box.schema.space.create('uid_to_tokenid')
            box.space.tokenid_to_tokeninfo:create_index('primary', {type = 'hash', parts = {1, 'STR'}})
         end


        function get_token(uid, tenant_id)  
                
            local token_id = sha512.crypt(os.clock())
            local issued_at_u = os.time()
            local expires_u = issued_at_u + 60 * 60;
            local issued_at_ = os.date("%Y-%m-%dT%H:%M:%S", issued_at_u)
            local expires_ = os.date("%Y-%m-%dT%H:%M:%S", expires_u)
            
            --insert in tarantool
            box.space.tokenid_to_tokeninfo:insert{token_id, uid, tenant_id, issued_at_, expires_}
            
            return token_id, issued_at_, expires_
        end

        local tenid_to_teninfo = {}
        tenid_to_teninfo = box.space.tenid_to_teninfo.index.secondary:get("admin")

        local tenant_id

        if not tenid_to_teninfo then --user doesn't exist
            tenant_id = uuid4.getUUID()
            box.space.tenid_to_teninfo:insert{tenant_id, "admin", nil, true}
        end

        local uid_to_uinfo = {}
        uid_to_uinfo = box.space.uid_to_uinfo.index.secondary:get("admin")
          
        local user_id
            
        if not uid_to_uinfo then --user doesn't exist
            user_id = uuid4.getUUID()
            box.space.uid_to_uinfo:insert{user_id, "admin", sha512.crypt("admin"), "123@email.com", true}
            box.space.uid_to_tenants:insert{user_id, tenant_id}
            get_token(user_id, tenant_id)
        end


        end
        )


