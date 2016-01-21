#!/usr/bin/python
import flask
from flask import Flask
from flask import jsonify
from flask import request
from sqlite3 import dbapi2 as sqlite

import hashlib
import datetime
from datetime import timedelta
import time

app = Flask(__name__)


PORT = 35357
PREFIX = "req-48a3eea2-0894-4ebd-a274-a0aa56"
COUNTER = 100000
HASH = hashlib.sha1()
SERVER_IP = "10.10.10.61"
DATABASE_SET = set()
DATABASE_PATH = "/var/lib/flask/iddb.sqlite"

class SQliteMng(object):
    def __init__(self):
        self.file_path = DATABASE_PATH 
        self.connection = sqlite.connect(self.file_path)
        self.connection.text_factory = str
        self.cursor = self.connection.cursor()
        self.cursor.execute("""\

	CREATE TABLE IF NOT EXISTS iddb (
		ID VARCHAR(50) NOT NULL

	)""")
    def addToken(self, id):
        try:
            self.cursor.execute("INSERT INTO iddb (ID) VALUES (?)", (id,))
        except Exception as e:
            print "ERROR:" + e
        return self.cursor.lastrowid

    def save(self):
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()

def set_custom_headers(headers):
    global COUNTER
    global PREFIX
    req_id = PREFIX + str(COUNTER)
    headers["x-openstack-request-id"] = req_id
    COUNTER += 1
    headers["Vary"] = "X-Auth-Token"
    # HTTP 1.1 doens't work!
    # headers["Keep-Alive"] = "timeout=5, max=100"
    # headers["Connection"] = "Keep-Alive"
    return


@app.route('/v2.0', methods=['GET'])
def v20():

    body = {'version': {'status': 'stable',
                        'updated': '2014-04-17T00:00:00Z',
                        'media-types':
                            [
                                {'base': 'application/json', 'type': 'application/vnd.openstack.identity-v2.0+json'}
                            ],
                        'id': 'v2.0',
                        'links':
                            [
                                {'href': 'http://' + SERVER_IP + ':35357/v2.0/', 'rel': 'self'},
                                {'href': 'http://docs.openstack.org/', 'type': 'text/html', 'rel': 'describedby'}
                            ]
                        }
            }
    resp = jsonify(body)
    set_custom_headers(resp.headers)
    return resp


@app.route('/v2.0/tokens', methods=['POST'])
def tokens():
    global HASH
    global SERVER_IP
    issued_at = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    expires = (datetime.datetime.now()+timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    HASH.update(str(time.time()))
    token_id = HASH.hexdigest()[-33:]
    global DATABASE_SET
    #DATABASE_SET.add(token_id)
    database.addToken(token_id)
    body = {
        "access": {
            "token": {
                "issued_at": issued_at,
                "expires": expires,
                "id": token_id,
                "tenant": {
                    "description": "Admin tenant",
                    "enabled": True,
                    "id": "6dcbaf4b07d64f91b87c4bc2ee8a0929",
                    "name": "admin"
                },
                "audit_ids": [
                    "A8a7LO3oShC9PuaHS9mfHQ"
                ]
            },
            "serviceCatalog": [
                {
                    "endpoints": [
                        {
                            "adminURL": "http://" + SERVER_IP + ":35357/v2.0",
                            "region": "RegionOne",
                            "internalURL": "http://" + SERVER_IP + ":5000/v2.0",
                            "id": "3e8987c7202d475a976d5b3c5d4d336e",
                            "publicURL": "http://" + SERVER_IP + ":5000/v2.0"
                        }
                    ],
                    "endpoints_links": [

                    ],
                    "type": "identity",
                    "name": "keystone"
                }
            ],
            "user": {
                "username": "admin",
                "roles_links": [

                ],
                "id": "90407f560e344ad39c6727a358278c35",
                "roles": [
                    {
                        "name": "_member_"
                    },
                    {
                        "name": "admin"
                    }
                ],
                "name": "admin"
            },
            "metadata": {
                "is_admin": 0,
                "roles": [
                    "9fe2ff9ee4384b1894a90878d3e92bab",
                    "be2b06f63ff84be595a18b1a1e2bb83d"
                ]
            }
        }
    }
    resp = jsonify(body)
    set_custom_headers(resp.headers)
    database.save()
    return resp


@app.route('/v2.0/tenants', methods=['POST'])
def tenants():
    global HASH
    global SERVER_IP
    HASH.update(str(time.time()))
    token_id = HASH.hexdigest()[-33:]
    global DATABASE_SET
    #DATABASE_SET.add(token_id)
    database.addToken(token_id)
    tenant_name = request.json["tenant"]["name"]
    body = {"tenant":
                {"description": "null",
                 "enabled": True,
                 "id": token_id,
                 "name": tenant_name
                 }
            }
    resp = jsonify(body)
    set_custom_headers(resp.headers)
    return resp


@app.route('/v2.0/users', methods=['POST'])
def users():
    global HASH
    global SERVER_IP
    HASH.update(str(time.time()))
    token_id = HASH.hexdigest()[-33:]
    global DATABASE_SET
    DATABASE_SET.add(token_id)
    user_name = request.json["user"]["name"]
    tenant_id = request.json["user"]["tenantId"]
    body = {"user":
                {"username": user_name,
                 "name": user_name,
                 "id": token_id,
                 "enabled": True,
                 "email": "c_rally_9aa720c3_lk5OUaDz@email.me",
                 "tenantId": tenant_id
                 }
            }
    resp = jsonify(body)
    set_custom_headers(resp.headers)
    return resp


@app.route('/', defaults={'path': ''}, methods=['DELETE'])
@app.route('/<path:path>', methods=['DELETE'])
def delete(path):
    return ""

from werkzeug.serving import WSGIRequestHandler
import logging
if __name__ == '__main__':
    #WSGIRequestHandler.protocol_version = "HTTP/1.1"
    database = SQliteMng()
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=35357)
    print "END"
    database.close()
