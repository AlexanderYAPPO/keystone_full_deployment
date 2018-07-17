from pprint import pprint
from time import sleep
import requests
#import pdb
#pdb.set_trace()
class DoStuff():

    def __init__(self):
        self.host = 'http://localhost:8001'
        self.domain_id = ''
        self.project_id = ''
        self.user_id = ''
        self.group_id = ''
        self.role_id = ''
        #return
        body = {
            "name": "mockbin",
            "upstream_url": "http://mockbin.org/request",
            "uris": "/"
        }    
        self.res = requests.post(self.host + '/apis', json = body)
        #self.checkCode(200)
        body = {
            "name": "keystone",
            "config.identity_provider": "fernet",
            "config.redis_port": "6379",
            "config.redis_host": "REDIS_IP",
            "config.redis_timeout": "2000",
            "config.redis_password": "",
            "config.max_active_fernet_keys": "3"
        }    
        self.res = requests.post(self.host + '/apis/mockbin/plugins', json = body)
        #self.checkCode(200)

        self.res = requests.post(self.host + '/v3', json = {})
        sleep(5)
        self.checkCode(200)
        body = {
	                "auth": {
		                "scope": {
			                "project": {
				                "domain": {
					                "name": "admin"
				                },
				                "name": "admin"
			                }
		                },
		                "identity": {
			                "password": {
				                "user": {
					                "domain": {
						                "name": "admin"
					                },
					                "password": "tester",
					                "name": "admin"
				                }
			                },
			                "methods": [
				                "password"
			                ]
		                }
	                }
                }
        self.res = requests.post(self.host + '/v3/auth/tokens', json = body)
        #print(self.res.json())
        token = self.res.headers["X-Subject-Token"]
        self.res = requests.post(self.host + '/v3/fernet_keys', json = {}, headers={'X-Auth-Token': token})
        # ids = self.res.json()
        # self.default_domain_id = ids['default_domain_id']
        # self.admin_domain_id = ids['admin_domain_id']
        # self.admin_project_id = ids['admin_project_id']
        # self.default_role_id = ids['default_role_id']
        # self.admin_role_id = ids['admin_role_id']
        # self.admin_user_id = ids['admin_user_id']

        body = {
            "region": {
                "description": "My subregion",
                "id": "RegionOne"
            }
        }
        self.res = requests.post(self.host + '/v3/regions/', json=body, headers={'X-Auth-Token': token})
        self.checkCode(201)
        #try:
        self.region_id = "RegionOne"#self.res.json()['region']['id']
        #except KeyError:
        #    self.region_id = 'RegionOne'    

        body = {
            "service": {
                "type": "identity",
                "name": "identity",
                "description": "identity service",
                "enabled": True
            }
        }
        self.res = requests.post(self.host + '/v3/services', json=body, headers={'X-Auth-Token': token})
        print(self.res.json())
        self.checkCode(201)
        #try:
        self.identity_service_id = self.res.json()['service']['id']
        #except KeyError:
        #    pass
            #try:
        body = {
        "endpoint": {
            "interface": "internal",
            "region_id": "RegionOne",
            "url": "http://HAPROXY_IP_HERE:8001/v3/",
            "service_id": self.identity_service_id
        }
        }

        self.res = requests.post(self.host  + '/v3/endpoints/', json=body, headers={'X-Auth-Token': token})

        self.checkCode(201)

        body = {
            "endpoint": {
            "interface": "public",
            "region_id": "RegionOne",
            "url": "http://HAPROXY_IP_HERE:8001/v3/",
            "service_id": self.identity_service_id
        }
        }
        self.res = requests.post(self.host + '/v3/endpoints/', json=body, headers={'X-Auth-Token': token})
        self.checkCode(201)

        body = {
         "endpoint": {
                "interface": "admin",
                "region_id": "RegionOne",
                "url": "http://HAPROXY_IP_HERE:8001/v3/",
                "service_id": self.identity_service_id
         }
        }
        self.res = requests.post(self.host + '/v3/endpoints/', json=body, headers={'X-Auth-Token': token})
        self.checkCode(201)

    def checkCode(self, code):
        if self.res.status_code != code:
          print("Failed with error:", self.res.reason)

"""
    body = {
        "domain": {
            "name": "Default",
            "description": "Default domain for testing",
            "enabled":  True
        }
    }
    self.res = requests.get(self.host + '/v3/domains/')
domains = self.res.json()['domains']
    for domain in domains:
    if domain['name'] == 'Default':
            self.domain_id = domain['id']
            break
print(self.domain_id)
#self.domain_id = self.res.json()['domain']['id']        
self.checkCode(201)

    body = {
        "project": {
            "name": "admin",
            "description": "Admin project for testing",
            "enabled": True,
            "is_domain": False,
            "domain_id": self.domain_id
        }
    }
    self.res = requests.post(self.host + '/v3/projects/', json = body)
self.project_id = self.res.json()['project']['id']
self.checkCode(201)

#body = {
    #    "user": {
    #        "enabled": "true",
    #        "name": "admin",
    #        "password": "tester",
    #        'default_project_id': self.project_id
    #        # "domain_id": self.domain_id,
    #    }
    #}
body = {
    "user": {
    "default_project_id": self.project_id,
    "domain_id": self.domain_id,
    "enabled": True,
    "name": "admin",
    "password": "tester",
    "description": "test admin",
    "email": "test@example.com"
    }
}

    self.res = requests.post(self.host + '/v3/users/', json = body)
    #self.checkCode(201)
    print(self.res.json())
    self.res = requests.get(self.host + '/v3/users/')
user_id = self.res.json()['users'][0]["id"]
    ###self.user_id = self.res.json()['user']['id']

body = {
        'role' : {
            'name' : 'admin',
            'domain_id' : self.domain_id
        }
    }
    self.res = requests.post(self.host + '/v3/roles/', json = body)
    self.checkCode(201)
#self.role_id = self.res.json()['role']['id']
    p = ['domain_id', 'project_id', 'user_id', 'group_id']#, 'role_id']
    for k in p:
        if self.__getattribute__(k) != '':
            print('self.' + k + ' = \''+ self.__getattribute__(k) + '\'')
"""    

        
if __name__ == '__main__':
    do_stuff = DoStuff()
