local server = require('http.server')
--local log = require('log')
local json = require('lunajson')
local sha512 = require('sha512')
local net_box = require('net.box')
local uuid4 = require('uuid4')
local shard = require('shard')

local SERVER_IP = '127.0.0.1'
local HOST = '0.0.0.0'
local PORT = 35357

--local PREFIX = "req-48a3eea2-0894-4ebd-a274-a0aa56"
local ERROR = 413

box.cfg{}
conn = net_box.connect('127.0.0.1:3311')
"replicator:password@{{hostvars[groups[cluster_name + '-slave-%d' | format(item)][0]  ].openstack.private_v4}}:3304",
local cfg = {
    servers = {
{% for item in range(1, n_slaves|int + 1) %}
    {uri = '{{hostvars[groups[cluster_name + '-slave-%d' | format(item)][0]  ].openstack.private_v4}}:3311', zone = {{'%d'| format(item)}} }, 

{% endfor %}
    }, 
    login = 'lena', 
    password = 'password',
    redundancy = 1, 
    binary = 3311
}

shard.init(cfg)

function print_r ( t )  
    local print_r_cache={}
    local function sub_print_r(t,indent)
        if (print_r_cache[tostring(t)]) then
            print(indent.."*"..tostring(t))
        else
            print_r_cache[tostring(t)]=true
            if (type(t)=="table") then
                for pos,val in pairs(t) do
                    if (type(val)=="table") then
                        print(indent.."["..pos.."] => "..tostring(t).." {")
                        sub_print_r(val,indent..string.rep(" ",string.len(pos)+8))
                        print(indent..string.rep(" ",string.len(pos)+6).."}")
                    elseif (type(val)=="string") then
                        print(indent.."["..pos..'] => "'..val..'"')
                    else
                        print(indent.."["..pos.."] => "..tostring(val))
                    end
                end
            else
                print(indent..tostring(t))
            end
        end
    end
    if (type(t)=="table") then
        print(tostring(t).." {")
        sub_print_r(t,"  ")
        print("}")
    else
        sub_print_r(t,"  ")
    end
    print()
end

function set_custom_headers()
	--local req_id = PREFIX .. COUNTER
    local headers = {}
    headers["x-openstack-request-id"] = uuid4.getUUID() -- uuid (uuid4)
    headers.Vary = "X-Auth-Token"
    return headers
end

function v20(req)
    if req.method ~= 'GET' then
        return
    end
    
    local body = {
            version = {
                status = 'stable',
                updated = '2014-04-17T00:00:00Z',
                id = 'v2.0',
                ['media-types'] = {{
                    base = 'application/json',
                    type = 'application/vnd.openstack.identity-v2.0+json'
                }},
                links = {
                    {href = 'http://' .. SERVER_IP .. ':35357/v2.0/', rel = 'self'},
                    {href = 'http://docs.openstack.org/', type = 'text/html', rel = 'describedby'}
                }
        }
    }

    local response = {}
    response.body = json.encode(body)
	response.headers = set_custom_headers()
	return response
end

--generate token and insert it in tarantool

function get_token(uid, tenant_id)  
        
	local token_id = sha512.crypt(os.clock())
	local issued_at_u = os.time()
	local expires_u = issued_at_u + 60 * 60;
	local issued_at_ = os.date("%Y-%m-%dT%H:%M:%S", issued_at_u)
	local expires_ = os.date("%Y-%m-%dT%H:%M:%S", expires_u)
    
    --insert in tarantool
    shard.tokenid_to_tokeninfo:insert{token_id, uid, tenant_id, issued_at_, expires_}
    --shard.uid_to_tokenid:insert{uid, token_id}
    return token_id, issued_at_, expires_
end


function tokens(req)
    if req.method ~= 'POST' then
        return
    end
    local request = req:json()
    
   -- local username_ = request.auth.identity.password.user.name
    local username_ = request.auth.passwordCredentials.username
   local password = sha512.crypt(request.auth.passwordCredentials.password)
    local ten_name = request.auth.tenantName
    --local tenant_id = request.auth.tenant.id
    local uname_to_uid = {}
    uname_to_uid = (shard.uname_to_uid:select({username_}))[1][1]

    local response = {}
    if #uname_to_uid == 0 then --user doesn't exist
        response.status = ERROR
        local body = {err = "user doesn't exist"}
        --print("bad user")
        response.body = json.encode(body)
	    return response
    end
    
    local uid = uname_to_uid[2]
    local uid_to_uinfo = {}
    uid_to_uinfo = (shard.uid_to_uinfo:select({uid}))[1][1]

    local upass = uid_to_uinfo[3]

    --if upass ~= password then
    if not sha512.verify(request.auth.passwordCredentials.password, upass) then
        response.status = ERROR
        local body = {err = "bad password"}
        --print("bad password")
        response.body = json.encode(body)
	    return response --incorrect password
    end

    local uid_to_tenants = {}
    uid_to_tenants = (shard.uid_to_tenants:select({uid}))[1][1]
    local is_tenant_exists = false

    local tenname_to_tenid = {}
    tenname_to_tenid = (shard.tenname_to_tenid:select({ten_name}))[1][1]
    
     if #tenname_to_tenid == 0 then --user doesn't exist
        response.status = ERROR
        local body = {err = "tenant doesn't exist"}
        response.body = json.encode(body)
	    return response
    end
    
    local tenant_id = tenname_to_tenid[2]
    
    local tenid_to_teninfo = {}
    tenid_to_teninfo = (shard.tenid_to_teninfo:select({tenant_id}))[1][1]

    for i = 2, #uid_to_tenants do
        if uid_to_tenants[i] == tenant_id then
            is_tenant_exists = true
            break
        end
    end
    
    if not is_tenant_exists then --user doesn't belong to this tenant
        response.status = ERROR
        local body = {err = "bad tenant id", uid = uid_to_tenants[1][2], tenant_id_ = tenant_id}
        response.body = json.encode(body)
	    return response
    end
            
    local token_id
	local issued_at_
	local expires_ 
    
    token_id, issued_at_, expires_ = get_token(uid, tenant_id)
    --local tenid_to_teninfo = {}
    --tenid_to_teninfo = box.space.tenid_to_teninfo:get(tenant_id)
    
   -- local ten_name = tenid_to_teninfo[2]
    local ten_description = tenid_to_teninfo[3]
    local ten_enabled = tenid_to_teninfo[4]
    
	local body = {
					access = {
							token = {
								issued_at = issued_at_,
								expires = expires_,
								id = token_id,
								tenant = {
										description = ten_description, --"Admin tenant",
										enabled = ten_enabled, --true,
                                        id = tenant_id, --"6dcbaf4b07d64f91b87c4bc2ee8a0929",
                                        name = ten_name --"admin"
                                },
                                audit_ids = {"A8a7LO3oShC9PuaHS9mfHQ"}
                            },
                            serviceCatalog = {{
                                endpoints = {{
                                    adminURL = "http://" .. SERVER_IP .. ":35357/v2.0",
                                    region = "RegionOne",
                                    internalURL = "http://" .. SERVER_IP .. ":5000/v2.0",
                                    id = "3e8987c7202d475a976d5b3c5d4d336e",
                                    publicURL = "http://" .. SERVER_IP .. ":5000/v2.0"
                                }},
                                type = "identity",
                                name = "keystone"
                            }},
                            user = {
                                username = username_, --"admin",
                                id = uid, --"90407f560e344ad39c6727a358278c35",
                                roles = {
                                    {name = "_member_"},
                                    {name = "admin"}
                                },
                                name = "admin"
                            },
                            metadata = {
                                is_admin = 0,
                                roles = {
                                    "9fe2ff9ee4384b1894a90878d3e92bab",
                                    "be2b06f63ff84be595a18b1a1e2bb83d"
                                    }
                            }
                        }
                    }

    response.body = json.encode(body)
	response.headers = set_custom_headers()
	return response
end

function tenants(req)
    if req.method ~= 'POST' then
        return
    end
    local request = req:json()
    
	local tenant_name = request.tenant.name
    
     -- return with error if tenant exists
    local select_res = {}
    select_res = (shard.tenname_to_tenid:select({tenant_name}))[1]
    
    local response = {}
    
    if #select_res ~= 0 then
      --return ERROR
        response.status = ERROR
	    return response
    end
    
    --insert in tarantool
    local tenant_id = uuid4.getUUID()
    
    shard.tenid_to_teninfo:insert{tenant_id, tenant_name, nil, true}
    shard.tenname_to_tenid:insert{tenant_name, tenant_id}
    --print("tenant id is " .. tenant_id)
    --local test_sha_ = sha2.sha512hex(tenant_name) --sha openssl
	local body = {
					tenant = {
								description = nil,
								enabled = true,
								id = tenant_id,
								name = tenant_name
								--test_sha = test_sha_
							 }
				 }
	
    response.body = json.encode(body)
	response.headers = set_custom_headers()
	return response
end

function users(req)
    if req.method ~= 'POST' then
        return
    end
    
	local request = req:json()
	local user_name = request.user.name
	local tenant_id = request.user.tenantId

	local passwd = sha512.crypt(request.user.password)-- sha512_crypt(request.user.password) --sha2.sha512hex(request.user.password)
	local email_ = request.user.email
	
	local response = {}
	
	if not tenant_id then
	    response.status = ERROR
	    --print("Error: tenant doesn't exist")
	    --print("tenant id is " .. tenant_id)
	    return response --413
	end
    
    -- return with error if user exists
    local select_res = {}
    select_res = (shard.uname_to_uid:select({user_name}))[1]
    if #select_res ~= 0 then
        response.status = ERROR
        --print("Error: user with this name exists")
        --print("user name is " .. user_name)
	    return response
    end
    
    local user_id = uuid4.getUUID()
    
    shard.uid_to_uinfo:insert{user_id, user_name, passwd, email_, true}
    shard.uid_to_tenants:insert{user_id, tenant_id}
    shard.uname_to_uid:insert{user_name, user_id}
    
    -- get token_id
    local token_id
    
    --print("user " .. user_name .. " is created")
    
   -- token_id = get_token(user_id, tenant_id)
    
	local body = {
					user = {
					        username = user_name,
							name = user_name,
							id = user_id,
							enabled = true,
							email = email_, --'c_rally_9aa720c3_lk5OUaDz@email.me',
							tenantID = tenant_id
						   }
				}
	
    response.body = json.encode(body)
	response.headers = set_custom_headers()
	return response

end

function delete(req)
    if req.method ~= 'DELETE' then
        return ""
    end
    
    --local response = {}
   -- local body = ""
    --response.body = {}--json.encode(body)
	return ""--response
end

function delete_tenant(req)
    local ten_id = req:stash('tenant_id')
    --print(ten_id)
    
    local tenid_to_teninfo = {}
    tenid_to_teninfo = (shard.tenid_to_teninfo:select({ten_id}))[1][1]
    
    local response = {}
    
    if #tenid_to_teninfo == 0 then --user doesn't exist
        response.status = ERROR
        local body = {err = "tenant doesn't exist"}
        response.body = json.encode(body)
	    return response
    end
    
    local tenant_name = tenid_to_teninfo[2]
    shard.tenid_to_teninfo:delete({ten_id})
    shard.tenname_to_tenid:delete({tenant_name})
    return response
end

function delete_user(req)
    local uid = req:stash('user_id')
    
    local uid_to_uinfo = {}
    uid_to_uinfo = (shard.uid_to_uinfo:select({uid}))[1][1]
    
    local response = {}
    
    if #uid_to_uinfo == 0 then --user doesn't exist
        response.status = ERROR
        local body = {err = "user doesn't exist"}
        response.body = json.encode(body)
	    return response
    end
    
    local uname = uid_to_uinfo[2] 
    shard.uid_to_uinfo:delete({uid})
    shard.uname_to_uid:delete({uname})
    return response
end

function get_user_info(req)
    local uid = req:stash('user_id')
    
    local uid_to_uinfo = {}
    uid_to_uinfo = (shard.uid_to_uinfo:select({uid}))[1]
    
    local response = {}
    
    if #uid_to_uinfo == 0 then --user doesn't exist
        response.status = ERROR
        local body = {err = "user doesn't exist"}
        response.body = json.encode(body)
	    return response
    end
    
    local user_name = uid_to_uinfo[2]
    local body = {
					user = {
					        domain_id = "default",							
							enabled = true,
							id = user_id,
							links = {
							    self = "http://localhost:5000/v3/users/ec8fc20605354edd91873f2d66bf4fc4"
                            },
							name = user_name
						   }
				}
	
    response.body = json.encode(body)
	response.headers = set_custom_headers()
    return response
end


httpd = server.new(HOST, PORT)
httpd:route({path = '/v2.0'}, v20)
httpd:route({path = '/v2.0/tokens'}, tokens)
httpd:route({path = '/v2.0/tenants'}, tenants)
httpd:route({path = '/v2.0/users'}, users)
httpd:route({path = '/'}, delete)
httpd:route({path = '<path:path>'}, delete)
--httpd:route({method = 'GET', path = '/testing/:tenant_id/:secret_string'}, testing)
httpd:route({method = 'DELETE', path = '/v2.0/tenants/:tenant_id'}, delete_tenant)
httpd:route({method = 'DELETE', path = '/v2.0/users/:user_id'}, delete_user)
httpd:route({method = 'GET', path = '/v2.0/users/:user_id'}, get_user_info)
--httpd:route({path = '/:path'}, delete)
httpd:start()
