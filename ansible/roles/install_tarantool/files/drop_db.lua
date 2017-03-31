local net_box = require('net.box')

box.cfg{}
conn = net_box.connect('0.0.0.0:3303')


if box.space.uid_to_uinfo then
    box.space.uid_to_uinfo:drop()
end

if box.space.uid_to_tenants then
    box.space.uid_to_tenants:drop()
end

if box.space.tenid_to_teninfo then
    box.space.tenid_to_teninfo:drop()
end

if box.space.tokenid_to_tokeninfo then
    box.space.tokenid_to_tokeninfo:drop()
end
