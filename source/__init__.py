import os

from flask import Flask, request
from source.node import Node, getId, BootstrapNode

#router stuff
import requests
import json
import numpy as np
from source.lib import merge_dict
from source.message import *
import time
import pathlib

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=False)
        mode_enabled = os.environ.get("MODE_CONFIG", default="normal")
        if mode_enabled =="boot":
            print("configuring from configBOOTSTRAP.py")
            app.config.from_pyfile('configBOOTSTRAP.py', silent=False)
        if os.environ.get("SET_PORT") is not None:
            print("Port detected set to ", os.environ.get("SET_PORT"))
            app.config["THIS_IP"] = app.config["THIS_IP"].split(":")[0]+\
                        ":"+str(os.environ.get("SET_PORT"))
        else:
            print("Port not pre-set")
    else:
        # load the test config if passed in
        print("test config")
        app.config.from_mapping(test_config)

    print(app.config["IS_BOOTSTRAP"])
    if app.config["IS_BOOTSTRAP"]:
        thisNode=BootstrapNode(app.config["THIS_IP"])
    else:
        thisNode =Node(app.config["THIS_IP"],\
                        app.config["BOOTSTRAP_IP"],\
                        app.config["IS_BOOTSTRAP"])

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'+str(app.config["BOOTSTRAP_IP"]+ " is boot="+app.config["IS_BOOTSTRAP"])

    @app.route('/join', methods=['GET'])
    def join():
        join_req = thisNode.join()
        # result should have :
        # text -> successfuly joined the network. Assigned position ???
        # assigned_position -> ???
        # prev [ip]
        # next [ip]
        # status -> error or success
        if join_req["status"] == 'Error':
            print("error in joining")

        return join_req

    @app.route('/check_depart/<string:departee_id>',methods=['GET'])
    def check_depart(departee_id):
        while(False):
            pass #maybe stall command later

        id_ip_dict = thisNode.get_id_ip_dict()
        id_ip_dict.pop(int(departee_id))

        return json.dumps({"status": "Success",\
                        "text": f"successfuly departed node with IP: {departee_id}"})

    @app.route('/check_join/<string:joinee_ip>', methods=['GET'])
    def check_join(joinee_ip):
        '''
        checks a join request. Only allowed to be accessed by Bootstrap
        '''
        if not(app.config["IS_BOOTSTRAP"]):
            status="Error"
            msg="Not eligible for checking join request. Try again"
            print(msg)
            return json.dumps({"status": status, \
                                "msg": msg, \
                                })
        else:
            joinee_id, prev_ip, next_ip = thisNode.check_join(joinee_ip)

            status="Success"
            msg=f"Join was successful with id: {joinee_id}"

            return json.dumps({"status": status, \
                                "msg": msg, \
                                "assigned_position": joinee_id,\
                                "prev_ip": prev_ip,\
                                "next_ip": next_ip,\
                                })

    @app.route('/accept_join_next/<string:next_ip>/<string:next_id>')
    def accept_join_next(next_ip, next_id):
        '''
        Input: next node's ip
        route is accessed from current Node (middle)
        Route belongs to  previous Node (left)
        '''
        print(f"Set {next_ip} (id: {next_id}) as next ")
        thisNode.set_next(next_ip, next_id)
        return json.dumps({"status": "Success"
        })

    @app.route('/accept_join_prev/<string:prev_ip>/<string:prev_id>')
    def accept_join_prev(prev_ip, prev_id):
        '''
        Input: previous node's ip
        route is accessed from current Node (middle)
        Route belongs to  next Node (right)
        updates next's DHT
        returns current's DHT
        '''

        # previous node before accepting
        old_prev = thisNode.getPrev()
        if old_prev == None:
            old_prev = thisNode.getAssignedId()
        # set new previous
        thisNode.set_prev(prev_ip, prev_id)
        # new previous id
        print(f"Set ip:{prev_ip} (id: {prev_id}) as previous")

        # get current's (middle) DHT
        nodesDHT = thisNode.getDHT()
        # find number of new keys assigned to previous (middle)
        length = (int(prev_id) - int(old_prev)) % 10
        # find new keys
        new_keys = set([(int(old_prev) + i) % 10 for i in range(1,length+1)])
        newDHT = {i:nodesDHT[i] for i in nodesDHT.keys() if int(i) in new_keys}

        # update next's (right) DHT
        for i in newDHT.keys():
            nodesDHT.pop(i)

        return json.dumps({"status": "Success",
                            "DHT" : newDHT,
        })

    @app.route('/accept_depart_next/<string:next_ip>/<string:next_id>', methods=['GET'])
    def accept_depart_next(next_ip, next_id):
        thisNode.set_next(next_ip, next_id)
        return json.dumps({"status": 'Success', \
                            "updated next": next_id})

    @app.route('/accept_depart_prev/<string:prev_ip>/<string:prev_id>', methods=['POST'])
    def accept_depart_prev(prev_ip, prev_id):
        thisNode.set_prev(prev_ip, prev_id)
        #print("??????????????????????????")
        #print("RERERERERRE", request, request.json, request.data, request.form)
        departee_dict = dict(request.get_json())#("data")
        # print("departee dict: ", departee_dict)
        nodesDHT = thisNode.getDHT()

        newDHT = merge_dict(departee_dict, nodesDHT)
        #print("newDHT (__init__)", newDHT)
        thisNode.setDHT(newDHT)

        return json.dumps({"status": 'Success', \
                            "updated prev": prev_id, \
                            })

    @app.route('/overlay',methods=['GET'])
    def overlay():
        '''
        Returns overlay of network
        '''
        networkOverlay = thisNode.getOverlay()
        return json.dumps({"status": "Success", \
                            "Overlay": networkOverlay})

    @app.route('/add2overlay/',methods=['POST'])
    def add2overlay():
        overlay_msg_fields = dict(request.get_json())
        overlayMsg = OverlayMessage(overlay_msg_fields)
        if thisNode.getAssignedId() == overlay_msg_fields["sender_id"]:
            # set overlay response as done
            thisNode.setOverlayResponses(overlay_msg_fields["message_id"], overlay_msg_fields["data"])
            print(thisNode.getOverlayResponses())
            return json.dumps({"status": "Success", \
                            "msg": f"Overlay finished"})
        else:
            overlayMsg.update(thisNode.getAssignedId(), thisNode.getIp())
            # request on other node for add2overlay
            requests.post(f"http://{thisNode.getNextIp()}/add2overlay/",\
                            json=overlayMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
                            "msg": f"Forwarded overlay request to {thisNode.getNext()}"})


    @app.route('/wait4overlay/<string:cur_id>/<string:msg_id>', methods=['GET'])
    def wait4overlay(cur_id, msg_id):
        while (msg_id not in thisNode.getOverlayResponses()):
            time.sleep(1)
            print(type(msg_id), msg_id)
            print(thisNode.getOverlayResponses())
            pass
        return json.dumps({"status": "Success", "OverlayId":msg_id, "Overlay":thisNode.getOverlayResponses()[msg_id] })


    @app.route('/insert', methods=['POST'])
    def insert():
        '''
        Starts insertion of {key,value} pair
        '''
        # insertion_dict = requests.get_json()["data_dict"] #dictionary with insertion (key, val) pairs
        # for entry in insertion_dict:
        #     thisNode.insertToDht(entry, insertion_dict[entry])
        #
        # return json.dumps({"status": 'Success', \
        #                     }

        insert_msg_fields = dict(request.get_json()) #key_data:.., val_data:...
        msg_key, msg_val = insert_msg_fields["key_data"], insert_msg_fields["val_data"]
        insertionResult = thisNode.insert(msg_key, msg_val)

        return json.dumps({"status": "Success", \
                            "msg": f"Successful insertion of data ({msg_key}, {msg_val})"})

    @app.route('/propagate_insert/', methods=['POST'])
    def propagate_insert():
        '''
        Propagates the insertion message
        '''
        insert_msg_fields = dict(request.get_json()) #key_data:.., val_data:...

        msg_key, msg_val = \
        list(insert_msg_fields["data"].keys())[0], list(insert_msg_fields["data"].values())[0] #{k:v}

        hashkey = str(getId(msg_key))
        if hashkey in thisNode.getDHT().keys():
            thisNode.insertToDht(msg_key, hashkey, msg_val)

        if thisNode.getAssignedId() == insert_msg_fields["sender_id"]:
            #print("\x1b[32mMessage dict:\x1b[0m", insert_msg_fields)
            msg_id = insert_msg_fields['message_id']

            thisNode.setAck(msg_id, True)
            # set overlay response as done

            return json.dumps({"status": "Success", \
                            "msg": f"Insertion finished"})
        else:
            insertMsg = InsertionMessage(insert_msg_fields)
            #insertMsg.update(thisNode.getAssignedId(), thisNode.getIp())
            # request on other node for add2overlay
            requests.post(f"http://{thisNode.getNextIp()}/propagate_insert/",\
                            json=insertMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
                            "msg": f"Forwarded insert request to {thisNode.getNext()}"})



    @app.route('/wait4insert/<string:msg_id>', methods=['GET'])
    def wait4insert(msg_id):
        '''
        '''
        while (not thisNode.getAck()[msg_id]):
            # print("--------------------------------")
            # print(thisNode.getInsertAck)
            # print("--------------------------------")
            time.sleep(1)
            print(f"in wait with ack: {thisNode.getAck()}")
            #print(type(msg_id), msg_id)
            #print(thisNode.getOverlayResponses())
            pass
        return json.dumps({"status": "Success", "InsertionId":msg_id, "Insertion":thisNode.getAck()[msg_id] })

    @app.route('/depart', methods=['GET'])
    def depart():
        '''
        safely departs from P2P network.
        Every local node should call it before departing
        '''
        depart_req = thisNode.depart()

        if depart_req["status"] == 'Error':
            print("error in departing")

        return depart_req

    @app.route('/print_all', methods=['GET'])
    def print_all():
        '''
        prints caller whole DHT
        '''
        return json.dumps({"dict":thisNode.getDHT(), "keys":sorted(list(thisNode.getDHT().keys()))})
    @app.route('/delete_all', methods=['GET'])
    def delete_all():
        '''
        deletes caller's whole DHT
        '''
        tmp = thisNode.getDHT()
        tmp.clear()
        return json.dumps({"status": 'Success', \
                            })

    @app.route('/load_data_from_file', methods=['GET'])
    def load_data_from_file():
        '''
        Loads data from data directory. File should be named insert.txt
        Called only from Bootstrap Node when it joins the network and no other node
        has joined yet. Initializes Bootstraps DHT with the data from the file.
        '''
        DHT={}
        for i in range(10):
            DHT[str(i)] = {}

        print(pathlib.Path(__file__).parent.absolute())
        filepath=str(pathlib.Path(__file__).parent.absolute())+"/data/insert1.txt"
        #filepath="/data/insert.txt"
        with open(filepath) as f:
            for line in f:
                val = line.split(',')[-1][:-1]
                key = line.split(',')[0:-1]
                if len(key) > 1:
                    key = ','.join(key)
                hashnumber = str(getId(key[0]))
                if hashnumber in DHT:
                    #DHT[hashnumber].append((key[0], val)) #Value: (name, ip of peer)
                    DHT[hashnumber][key[0]]=val
                else:
                    #DHT[hashnumber] = [(key[0],val)]
                    DHT[hashnumber] = {key[0]:val}

        thisNode.setDHT(DHT)
        return json.dumps({"status": 'Success', \
                            })





    return app
