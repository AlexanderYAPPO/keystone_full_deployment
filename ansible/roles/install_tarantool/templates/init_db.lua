
local sha512 = require('sha512')
local net_box = require('net.box')
local uuid4 = require('uuid4')
local shard = require('shard')
--local p = require('connpool')



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


box.cfg{}
conn = net_box.connect('lena:password@127.0.0.1:3311')

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

--pool = p.new()

shard.init(cfg)

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

--shard.wait_connection()

local tenname_to_tenid = {}
tenname_to_tenid = (shard.tenname_to_tenid:select{"admin"})[1]

local tenant_id

if #tenname_to_tenid == 0 then --user doesn't exist
    tenant_id = uuid4.getUUID()
    shard.tenid_to_teninfo:insert{tenant_id, "admin", nil, true}
    shard.tenname_to_tenid:insert{"admin", tenant_id}
end

local uname_to_uid = {}
uname_to_uid = (shard.uname_to_uid:select{"admin"})[1]
  
local user_id
    
if #uname_to_uid == 0 then --user doesn't exist
    user_id = uuid4.getUUID()
    shard.uid_to_uinfo:insert{user_id, "admin", sha512.crypt("admin"), "123@email.com", true}
    shard.uid_to_tenants:insert{user_id, tenant_id}
    shard.uname_to_uid:insert{"admin", user_id}
    get_token(user_id, tenant_id)
end

