#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#   Reference:
#      https://github.com/uofa-cmput404/cmput404-slides/blob/a8843657fcca3a1c6006a2baf6dc5308893574d7/examples/ObserverExampleAJAX/inspid.py 
#      under the Apache License, Version 2.0, Copyright 2013 Abram Hindle and Copyright 2019 Hazel Victoria Campbell
#      
#      https://github.com/abramhindle/WebSocketsExamples/blob/547b31b1a6873dd67dc5a4a44cbed0a2003d7811/chat.py
#      under the Apache License, Version 2.0, Copyright 2013 Abram Hindle
#
#      https://github.com/abramhindle/WebSocketsExamples/blob/547b31b1a6873dd67dc5a4a44cbed0a2003d7811/broadcaster.py
#      under the Apache License, Version 2.0, Copyright 2013 Abram Hindle


import flask
from flask import Flask, request, redirect
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener(entity, self.get(entity))

    def clear(self):
        self.space = dict()
        try:
            for listener in self.listeners:
                listener(None, None)
        except:
            "no listeners yet"

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space

myWorld = World()     

clients = list()

def set_listener( entity, data ):
    ''' do something with the update ! '''
    # add to client queues
    for client in clients:
        client.put(json.dumps(myWorld.space))

myWorld.add_set_listener( set_listener )
        
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    return redirect("/static/index.html", code=302)

def read_ws(ws,client):
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME
    try:
        while True:
            msg = ws.receive()
            #print("WS RECV: %s" % msg)
            if (msg is not None):
                packet = json.loads(msg)
                for entity in packet.keys():
                    values = packet[entity].keys()
                    myWorld.set(entity, packet[entity])
                    '''if "x" in values:
                        myWorld.update(entity, "x", packet[entity]["x"])
                    if "y" in values:
                        myWorld.update(entity, "y", packet[entity]["y"])
                    if "colour" in values:
                        myWorld.update(entity, "colour", packet[entity]["colour"])
                    if "radius" in values:
                        myWorld.update(entity, "radius", packet[entity]["radius"])'''
            else:
                break
    except:
        '''Done'''

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # XXX: TODO IMPLEMENT ME
    print("WS:", ws)
    client = queue.Queue()
    clients.append(client)
    g = gevent.spawn( read_ws, ws, client )    
    try:
        while True:
            # block here
            msg = client.get()
            ws.send(msg)
    except Exception as e:# WebSocketError as e:
        print("WS Error %s" % e)
    finally:
        clients.remove(client)
        gevent.kill(g)


# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    dict = flask_post_json()
    if "x" in dict.keys():
        myWorld.update(entity, "x", dict["x"])
    if "y" in dict.keys():
        myWorld.update(entity, "y", dict["y"])
    if "colour" in dict.keys():
        myWorld.update(entity, "colour", dict["colour"])
    if "radius" in dict.keys():
        myWorld.update(entity, "radius", dict["radius"])
    return json.dumps(myWorld.get(entity))

@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    return json.dumps(myWorld.space)

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    return json.dumps(myWorld.get(entity))


@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    myWorld.clear()
    return json.dumps(myWorld.space)



if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
