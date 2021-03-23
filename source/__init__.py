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
import threading

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
        thisNode=BootstrapNode(app.config["THIS_IP"], \
                                app.config["N_REPLICAS"], \
                                app.config["POLICY"])
    else:
        thisNode =Node(app.config["THIS_IP"],\
                        app.config["BOOTSTRAP_IP"],\
                        app.config["N_REPLICAS"],\
                        app.config["IS_BOOTSTRAP"], \
                        app.config["POLICY"])

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #################################################################################################################
    ####################################### CLI COMMANDS ############################################################
    #################################################################################################################

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

    @app.route('/overlay',methods=['GET'])
    def overlay():
        '''
        Returns overlay of network
        '''
        networkOverlay = thisNode.getOverlay()
        return json.dumps({"status": "Success", \
                            "Overlay": networkOverlay})

    @app.route('/insert', methods=['POST'])
    def insert():
        '''
        Starts insertion of {key,value} pair
        '''

        insert_msg_fields = dict(request.get_json()) #key_data:.., val_data:...
        msg_key, msg_val = insert_msg_fields["key_data"], insert_msg_fields["val_data"]
        if thisNode.policy == "EVENTUAL":
            insertionResult = thisNode.insert_eventual(msg_key, msg_val)
        elif thisNode.policy == "CHAIN":
            insertionResult = thisNode.insert_chain(msg_key, msg_val)
        else:
            insertionResult = thisNode.insert(msg_key, msg_val)

        return json.dumps({"status": "Success", \
                            "msg": f"Successful insertion of data ({msg_key}, {msg_val})"})

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


    @app.route('/delete', methods=['POST'])
    def delete():
        '''
        Starts deletion of pair with given key.
        '''

        delete_msg_fields = dict(request.get_json()) #key_data:.., val_data:...
        msg_key= delete_msg_fields["key_data"]
        if thisNode.policy == "EVENTUAL":
            deletionResult = thisNode.delete_eventual(msg_key)
        elif thisNode.policy == "CHAIN":
            deletionResult = thisNode.delete_chain(msg_key)
        else:
            deletionResult = thisNode.delete(msg_key)
        return json.dumps({"status": "Success", \
                            "msg": f"Successful delete of key {msg_key}"})

    @app.route('/query', methods=['POST'])
    def query():
        '''
        Starts query for given key
        '''
        query_msg_fields = dict(request.get_json()) #key_data:.., val_data:...
        msg_key= query_msg_fields["key_data"]
        if thisNode.policy == "EVENTUAL":
            queryResult = thisNode.query_eventual(msg_key)
        elif thisNode.policy == "CHAIN":
            queryResult = thisNode.query_chain(msg_key)
        else:
            queryResult = thisNode.query(msg_key)

        return json.dumps({"status": "Success", \
                            "msg": f"Successful query result for key {msg_key} is value: {queryResult['queryValue']}"})

    @app.route('/queryall', methods=['GET'])
    def query_all():
        '''
        Returns every (key, value) pair stored in DHT for every node in the Network
        '''
        res = thisNode.query_all()
        return json.dumps({"status": "Success", \
                            "result": res})

    @app.route('/print_all', methods=['GET'])
    def print_all():
        '''
        prints caller whole DHT
        '''
        if app.config["N_REPLICAS"] <2:
            return json.dumps({"dict":thisNode.getDHT(),\
             "keys":sorted(list(thisNode.getDHT().keys()))})
        else:
            return json.dumps({"DHT":thisNode.getDHT(), \
                                "repl_DHT": thisNode.getReplDHT(), \
                            "keys":sorted(list(thisNode.getDHT().keys())), \
                                "repl_keys": sorted(list(thisNode.getReplDHT().keys()))})


    #################################################################################################################


    #################################################################################################################
    ############################################ JOIN ###############################################################
    #################################################################################################################


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
            joinee_id, prev_ip, next_ip, next_nodes, prev_nodes, overlay = thisNode.check_join(joinee_ip)

            status="Success"
            msg=f"Join was successful with id: {joinee_id}"

            return json.dumps({"status": status, \
                                "msg": msg, \
                                "assigned_position": joinee_id,\
                                "prev_ip": prev_ip,\
                                "next_ip": next_ip,\
                                "replicas": next_nodes,\
                                "prev_nodes": prev_nodes,\
                                "overlay": overlay
                                })


    @app.route('/accept_join_next/<string:next_ip>/<string:next_id>', methods=['GET'])
    def accept_join_next(next_ip, next_id):
        '''
        Input: next node's ip
        route is accessed from current Node (middle)
        Route belongs to  previous Node (left)
        '''
        print(f"Set {next_ip} (id: {next_id}) as next ")
        thisNode.set_next(next_ip, next_id)
        return json.dumps({"status": "Success"})

    @app.route('/accept_join_prev/<string:prev_ip>/<string:prev_id>', methods=['GET'])
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

    #################################################################################################################

    #################################################################################################################
    ############################################ DEPART #############################################################
    #################################################################################################################

    @app.route('/check_depart/<string:departee_id>',methods=['GET'])
    def check_depart(departee_id):
        while(False):
            pass #maybe stall command later

        if not(app.config["IS_BOOTSTRAP"]):
            status="Error"
            msg="Not eligible for checking depart request. Try again"
            print(msg)
            return json.dumps({"status": status, \
                                "msg": msg, \
                                })

        n_prev_nodes, overlay = thisNode.check_depart(departee_id)

        return json.dumps({"status": "Success",\
                        "text": f"successfuly departed node with IP: {departee_id}", \
                        "prev_nodes": n_prev_nodes, \
                        "overlay": overlay})




    @app.route('/accept_depart_next/<string:next_ip>/<string:next_id>', methods=['GET'])
    def accept_depart_next(next_ip, next_id):
        thisNode.set_next(next_ip, next_id)
        return json.dumps({"status": 'Success', \
                            "updated next": next_id})

    @app.route('/accept_depart_prev/<string:prev_ip>/<string:prev_id>', methods=['POST'])
    def accept_depart_prev(prev_ip, prev_id):
        thisNode.set_prev(prev_ip, prev_id)

        departee_dict = dict(request.get_json())#("data")

        nodesDHT = thisNode.getDHT()

        newDHT = merge_dict(departee_dict, nodesDHT)

        thisNode.setDHT(newDHT)

        return json.dumps({"status": 'Success', \
                            "updated prev": prev_id, \
                            })

    #################################################################################################################

    #################################################################################################################
    ############################################ OVERLAY ############################################################
    #################################################################################################################


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

    #################################################################################################################

    #################################################################################################################
    ############################################ INSERT #############################################################
    #################################################################################################################


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
            # current node has the appropriate hashkey row.
            # therefore add/edit current node's DHT
            thisNode.insertToDht(msg_key, hashkey, msg_val)
            # prepare ack-message's data dictionary
            ack_dict = insert_msg_fields.copy()
            ack_dict["ack_sender_id"] = thisNode.getAssignedId()
            # consturct ack message
            ackMsg = AcknowledgeMessage(ack_dict)
            # propagate ack message to next id
            requests.post(f"http://{thisNode.getNextIp()}/propagate_insert_ack/",\
                            json=ackMsg.__dict__)

            return  json.dumps({"status": "Success", \
                            "msg": f"Forwarded insert acknowledge to {thisNode.getNext()}"})

        # if thisNode.getAssignedId() == insert_msg_fields["sender_id"]:
        #     # this should not be reachable
        #     msg_id = insert_msg_fields['message_id']
        #
        #     thisNode.setAck(msg_id, True)
        #     # set overlay response as done
        #
        #     return json.dumps({"status": "Success", \
        #                     "msg": f"Insertion finished"})
        else:
            # message has not reached appropriate node.
            # Propagate insertion message to next node

            insertMsg = InsertionMessage(insert_msg_fields)
            #insertMsg.update(thisNode.getAssignedId(), thisNode.getIp())
            requests.post(f"http://{thisNode.getNextIp()}/propagate_insert/",\
                            json=insertMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
                            "msg": f"Forwarded insert request to {thisNode.getNext()}"})

    def propagate_insert_repl(insert_msg_fields):
        '''
        Propagates the insertion message
        '''
        #insert_msg_fields = dict(request.get_json()) #key_data:.., val_data:...


        msg_key, msg_val = \
            list(insert_msg_fields["data"].keys())[0], list(insert_msg_fields["data"].values())[0] #{k:v}

        # update message dictionary with updated replica counter
        insert_msg_fields_copy = insert_msg_fields.copy()
        # insert_msg_fields_copy['replica_counter'] = replica_counter

        hashkey = str(getId(msg_key))
        if hashkey in thisNode.repl_DHT.keys():
            # current node has (should!) the appropriate hashkey row in replica DHT.
            # therefore add/edit current node's replica DHT

            thisNode.insertToReplDht(msg_key, hashkey, msg_val)
            replica_counter = insert_msg_fields["replica_counter"] - 1

        else:
            replica_counter = insert_msg_fields["replica_counter"]

        print("\x1b[32mReplica counter\x1b[0m", replica_counter)

        if replica_counter != 0:
            # message has not reached last replica node.
            # Propagate insertion repl message to next node
            insertMsg = InsertionMessage(insert_msg_fields_copy, replica_counter=replica_counter)
            #insertMsg.update(thisNode.getAssignedId(), thisNode.getIp())
            requests.post(f"http://{thisNode.getNextIp()}/threading_replicas/Insertion",\
                            json=insertMsg.__dict__)

        return  json.dumps({"status": "Success", \
                        "msg": f"Updated replica with id {thisNode.getAssignedId()}"})


    @app.route('/propagate_insert_ack/', methods=['POST'])
    def propagate_insert_ack():
        ack_msg_fields = dict(request.get_json())
        if thisNode.getAssignedId() == ack_msg_fields["sender_id"]:
            #print("\x1b[32mMessage dict:\x1b[0m", insert_msg_fields)
            msg_id = ack_msg_fields['message_id']

            thisNode.setAck(msg_id, True)
            # set overlay response as done

            return json.dumps({"status": "Success", \
                            "msg": f"Insertion finished"})
        else:
            ackMsg = AcknowledgeMessage(ack_msg_fields)
            #insertMsg.update(thisNode.getAssignedId(), thisNode.getIp())
            # request on other node for add2overlay
            requests.post(f"http://{thisNode.getNextIp()}/propagate_insert_ack/",\
                            json=ackMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
            "msg": f"Forwarded insert acknowledge to {thisNode.getNext()}"})

    @app.route('/propagate_insert_2manager/', methods=['POST'])
    def propagate_insert_2manager():
        '''
        Propagates the insertion message to replica manager.
        '''
        insert_msg_fields = dict(request.get_json()) #key_data:.., val_data:...
        print("\x1b[36mDict:\x1b[0m", insert_msg_fields)

        msg_key, msg_val = \
            list(insert_msg_fields["data"].keys())[0], list(insert_msg_fields["data"].values())[0] #{k:v}

        hashkey = str(getId(msg_key))
        if hashkey in thisNode.getDHT().keys():
            # current node has the appropriate hashkey row.
            # therefore message has arrived at replica manager for this hashkey
            thisNode.insertToDht(msg_key, hashkey, msg_val)
            print("Counter:", insert_msg_fields["replica_counter"])
            if thisNode.getPolicy() == "EVENTUAL":
                x = threading.Thread(target=propagate_insert_repl, args = [insert_msg_fields])
                x.start()
            elif thisNode.getPolicy() == "CHAIN":
                mode = "Insertion"
                insert_req = (requests.post(f"http://{thisNode.getNextIp()}/threading_replicas/{mode}", json=insert_msg_fields)).json()


            ack_dict = insert_msg_fields.copy()
            ack_dict["ack_sender_id"] = thisNode.getAssignedId()
            # consturct ack message
            ackMsg = AcknowledgeMessage(ack_dict)
            # propagate ack message to next id
            req = requests.post(f"http://{thisNode.getNextIp()}/propagate_insert_ack/",\
                            json=ackMsg.__dict__)

            return  json.dumps({"status": "Success", \
                            "msg": f"Forwarded insert acknowledge to {thisNode.getNext()}"})
            if thisNode.policy == "EVENTUAL":
                x.join()


        else:
            # message has not reached appropriate node.
            # Propagate insertion message to next node

            insertMsg = InsertionMessage(insert_msg_fields, replica_counter=insert_msg_fields["replica_counter"], direction=insert_msg_fields["direction"])
            #insertMsg.update(thisNode.getAssignedId(), thisNode.getIp())
            # \add/edit current node's DHT

            if insertMsg.direction == 'l':
                ip = thisNode.getPrevIp()
                id = thisNode.getPrev()
            else:
                ip = thisNode.getNextIp()
                id = thisNode.getNext()

            requests.post(f"http://{ip}/propagate_insert_2manager/",
                            json=insertMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
                            "msg": f"Forwarded insert request to {id}"})


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


    #################################################################################################################
    ############################################ DELETE #############################################################
    #################################################################################################################


    def propagate_delete_repl(delete_msg_fields):
        '''
        Propagates the deletion message
        '''
        #insert_msg_fields = dict(request.get_json()) #key_data:.., val_data:...


        msg_key = delete_msg_fields["data"]

        # update message dictionary with updated replica counter
        delete_msg_fields_copy = delete_msg_fields.copy()
        # insert_msg_fields_copy['replica_counter'] = replica_counter

        hashkey = str(getId(msg_key))
        if hashkey in thisNode.repl_DHT.keys():
            # current node has (should!) the appropriate hashkey row in replica DHT.
            # therefore add/edit current node's replica DHT

            print("\x1b[32mRepl DHT keys\x1b[0m", thisNode.repl_DHT.keys())
            print("\x1b[32mHashkey\x1b[0m:", hashkey)

            thisNode.deleteFromReplDht(msg_key, hashkey)
            replica_counter = delete_msg_fields["replica_counter"] - 1

        else:
            replica_counter = delete_msg_fields["replica_counter"]

        print("\x1b[32mReplica counter\x1b[0m", replica_counter)

        if replica_counter != 0:
            # message has not reached last replica node.
            # Propagate insertion repl message to next node
            deleteMsg = DeletionMessage(delete_msg_fields_copy, replica_counter=replica_counter)
            #insertMsg.update(thisNode.getAssignedId(), thisNode.getIp())
            requests.post(f"http://{thisNode.getNextIp()}/threading_replicas/Deletion",\
                            json=deleteMsg.__dict__)

        return  json.dumps({"status": "Success", \
                        "msg": f"Deleted replica with id {thisNode.getAssignedId()}"})



    @app.route('/propagate_delete/', methods=['POST'])
    def propagate_delete():
        '''
        Propagates the deletion message
        '''
        delete_msg_fields = dict(request.get_json()) #key_data:.., val_data:...

        msg_key = delete_msg_fields["data"]

        hashkey = str(getId(msg_key))
        if hashkey in thisNode.getDHT().keys():
            # current node has the appropriate hashkey row.
            # therefore delete from current node's DHT
            thisNode.deleteFromDht(msg_key, hashkey)
            # prepare ack-message's data dictionary
            ack_dict = delete_msg_fields.copy()
            ack_dict["ack_sender_id"] = thisNode.getAssignedId()
            # consturct ack message
            ackMsg = AcknowledgeMessage(ack_dict)
            # propagate ack message to next id
            requests.post(f"http://{thisNode.getNextIp()}/propagate_delete_ack/",\
                            json=ackMsg.__dict__)

            return  json.dumps({"status": "Success", \
                            "msg": f"Forwarded delete acknowledge to {thisNode.getNext()}"})


        else:
            # message has not reached appropriate node.
            # Propagate insertion message to next node

            deleteMsg = DeletionMessage(delete_msg_fields)
            #insertMsg.update(thisNode.getAssignedId(), thisNode.getIp())
            requests.post(f"http://{thisNode.getNextIp()}/propagate_delete/",\
                            json=deleteMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
                            "msg": f"Forwarded deletion request to {thisNode.getNext()}"})

    @app.route('/propagate_delete_ack/', methods=['POST'])
    def propagate_delete_ack():
        ack_msg_fields = dict(request.get_json())
        if thisNode.getAssignedId() == ack_msg_fields["sender_id"]:
            #print("\x1b[32mMessage dict:\x1b[0m", insert_msg_fields)
            msg_id = ack_msg_fields['message_id']

            thisNode.setAck(msg_id, True)
            # set overlay response as done

            return json.dumps({"status": "Success", \
                            "msg": f"Deletion finished"})
        else:
            ackMsg = AcknowledgeMessage(ack_msg_fields)
            #insertMsg.update(thisNode.getAssignedId(), thisNode.getIp())
            # request on other node for add2overlay
            requests.post(f"http://{thisNode.getNextIp()}/propagate_delete_ack/",\
                            json=ackMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
            "msg": f"Forwarded deletion acknowledge to {thisNode.getNext()}"})

    @app.route('/propagate_delete_2manager/', methods=['POST'])
    def propagate_delete_2manager():
        '''
        Propagates the deletion message to replica manager.
        '''
        delete_msg_fields = dict(request.get_json()) #key_data:.., val_data:...
        print("\x1b[36mDict:\x1b[0m", delete_msg_fields)

        msg_key = delete_msg_fields["data"]

        hashkey = str(getId(msg_key))
        if hashkey in thisNode.getDHT().keys():
            # current node has the appropriate hashkey row.
            # therefore message has arrived at replica manager for this hashkey
            thisNode.deleteFromDht(msg_key, hashkey)
            print("Counter:", delete_msg_fields["replica_counter"])
            if thisNode.getPolicy() == "EVENTUAL":
                y = threading.Thread(target=propagate_delete_repl, args = [delete_msg_fields])
                y.start()
            elif thisNode.getPolicy() == "CHAIN":
                delete_req = (requests.post(f"http://{thisNode.getNextIp()}/threading_replicas/Deletion", json=delete_msg_fields)).json()
            else:
                print("Policy should be one of [EVENTUAL|POLICY] when using propagate_delete_2manager")

            ack_dict = delete_msg_fields.copy()
            ack_dict["ack_sender_id"] = thisNode.getAssignedId()
            # consturct ack message
            ackMsg = AcknowledgeMessage(ack_dict)
            # propagate ack message to next id
            req = requests.post(f"http://{thisNode.getNextIp()}/propagate_delete_ack/",\
                            json=ackMsg.__dict__)

            return  json.dumps({"status": "Success", \
                            "msg": f"Forwarded delete acknowledge to {thisNode.getNext()}"})
            if thisNode.getPolicy == "EVENTUAL":
                y.join()


        else:
            # message has not reached appropriate node.
            # Propagate insertion message to next node

            deleteMsg = DeletionMessage(delete_msg_fields, replica_counter=delete_msg_fields["replica_counter"])
            # \add/edit current node's DHT
            requests.post(f"http://{thisNode.getNextIp()}/propagate_delete_2manager/",
                            json=deleteMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
                            "msg": f"Forwarded deletion request to {thisNode.getNext()}"})


    @app.route('/wait4delete/<string:msg_id>', methods=['GET'])
    def wait4delete(msg_id):
        '''
        Endpoint that waits for deletion
        '''
        while (not thisNode.getAck()[msg_id]):
            time.sleep(1)
            print(f"in wait with ack: {thisNode.getAck()}")
            pass

        return json.dumps({"status": "Success", "DeletionId":msg_id, "Deletion":thisNode.getAck()[msg_id] })

    #################################################################################################################

    #################################################################################################################
    ############################################ QUERY #############################################################
    #################################################################################################################



    @app.route('/threading_replicas/<string:mode>', methods=['POST'])
    def threading_replicas(mode):
        '''
        spawns threads for message propagation to replicas.
        mode: message's query type.
        '''
        if mode == "Insertion":
            insert_msg_fields = dict(request.get_json())
            res = propagate_insert_repl(insert_msg_fields)
        elif mode == "Deletion":
            delete_msg_fields = dict(request.get_json())
            res = propagate_delete_repl(delete_msg_fields)
        return res # gia na mhn petaei error 8elei pantote na epistrefei kati

    #@app.route('/propagate_insert_repl/', methods=['POST'])





    @app.route('/propagate_query/', methods=['POST'])
    def propagate_query():
        '''
        Propagates the deletion message
        '''
        query_msg_fields = dict(request.get_json()) #key_data:.., val_data:...

        msg_key = query_msg_fields["data"]

        hashkey = str(getId(msg_key))
        if hashkey in thisNode.getDHT().keys():
            # current node has the appropriate hashkey row.
            # therefore answer query from current node's DHT
            queryValue = thisNode.queryFromDht(msg_key, hashkey)
            # prepare ack-message's data dictionary
            ack_dict = query_msg_fields.copy()
            ack_dict["ack_sender_id"] = thisNode.getAssignedId()
            ack_dict["ack_result"] = queryValue
            # consturct ack message
            ackMsg = AcknowledgeMessage(ack_dict)
            #print("\x1b[31mDict:\x1b[0m", ackMsg.__dict__)
            # propagate ack message to next id
            requests.post(f"http://{thisNode.getNextIp()}/propagate_query_ack/",\
                            json=ackMsg.__dict__)

            return  json.dumps({"status": "Success", \
                            "msg": f"Forwarded query acknowledge to {thisNode.getNext()}"})

        else:
            # message has not reached appropriate node.
            # Propagate query message to next node
            queryMsg = QueryMessage(query_msg_fields)

            requests.post(f"http://{thisNode.getNextIp()}/propagate_query/",\
                            json=queryMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
                            "msg": f"Forwarded query request to {thisNode.getNext()}"})

    @app.route('/propagate_query_repl/', methods=['POST'])
    def propagate_query_repl():
        '''
        Propagates the query message
        '''
        query_msg_fields = dict(request.get_json()) #key_data:.., val_data:...
        msg_key = query_msg_fields["data"]


        hashkey = str(getId(msg_key))
        replica_counter = query_msg_fields["replica_counter"]
        print("\x1b[32mReplica Counter:\x1b[0m", replica_counter)

        if hashkey in thisNode.getReplDHT().keys():
            # update replica counter
            replica_counter = replica_counter- 1

            # ~~~~~~~~~~~EVENTUAL POLICY~~~~~~~~
            if thisNode.getPolicy() == 'EVENTUAL':
                # current node has the appropriate hashkey row.
                # therefore answer query from current node's DHT
                queryValue = thisNode.queryFromReplDht(msg_key, hashkey)
                # prepare ack-message's data dictionary
                ack_dict = query_msg_fields.copy()
                ack_dict["ack_sender_id"] = thisNode.getAssignedId()
                ack_dict["ack_result"] = queryValue
                # consturct ack message
                ackMsg = AcknowledgeMessage(ack_dict)
                #print("\x1b[31mDict:\x1b[0m", ackMsg.__dict__)
                # propagate ack message to next id
                requests.post(f"http://{thisNode.getNextIp()}/propagate_query_ack/",\
                                json=ackMsg.__dict__)

                return  json.dumps({"status": "Success", \
                            "msg": f"Forwarded query acknowledge to {thisNode.getNext()}"})

            # ~~~~~~~~~~~CHAIN POLICY~~~~~~~~
            else:
                # policy is : "CHAIN"
                # print("Replica counter:", replica_counter)
                if replica_counter != 0:
                    # this is not the last replica!
                    query_msg_fields_copy = query_msg_fields.copy()
                    query_msg_fields_copy["replica_counter"] = replica_counter
                    query_req = (requests.post(f"http://{thisNode.getNextIp()}/propagate_query_repl/", json=query_msg_fields_copy)).json()
                    return  json.dumps({"status": "Success", \
                                "msg": f"Forwarded query request to replica: {thisNode.getNext()}"})
                else:
                    queryValue = thisNode.queryFromReplDht(msg_key, hashkey)
                    # prepare ack-message's data dictionary
                    ack_dict = query_msg_fields.copy()
                    ack_dict["ack_sender_id"] = thisNode.getAssignedId()
                    ack_dict["ack_result"] = queryValue
                    # consturct ack message
                    ackMsg = AcknowledgeMessage(ack_dict)
                    #print("\x1b[31mDict:\x1b[0m", ackMsg.__dict__)
                    # propagate ack message to next id
                    requests.post(f"http://{thisNode.getNextIp()}/propagate_query_ack/",\
                                    json=ackMsg.__dict__)
                    return  json.dumps({"status": "Success", \
                                "msg": f"Forwarded query acknowledge to {thisNode.getNext()}"})


        else:
            # message has not reached appropriate (replica) node.
            # Propagate query message to next node
            queryMsg = QueryMessage(query_msg_fields, replica_counter = replica_counter)

            requests.post(f"http://{thisNode.getNextIp()}/propagate_query_repl/",\
                            json=queryMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
                            "msg": f"Forwarded query request to {thisNode.getNext()}"})

    @app.route('/propagate_query_2manager/', methods=['POST'])
    def propagate_query_2manager():
        '''
        Propagates the query message to replica manager.
        '''
        query_msg_fields = dict(request.get_json()) #key_data:.., val_data:...
        print("\x1b[36mDict:\x1b[0m", query_msg_fields)

        msg_key = query_msg_fields["data"]

        hashkey = str(getId(msg_key))
        if hashkey in thisNode.getDHT().keys():
            # current node has the appropriate hashkey row.
            # therefore message has arrived at replica manager for this hashkey

            query_req = (requests.post(f"http://{thisNode.getNextIp()}/propagate_query_repl/", json=query_msg_fields)).json()


            return  json.dumps({"status": "Success", \
                            "msg": f"Forwarded query 2 replica manager {thisNode.getNext()}"})


        else:
            # message has not reached appropriate node.
            # Propagate insertion message to next node

            queryMsg = QueryMessage(query_msg_fields, replica_counter=query_msg_fields["replica_counter"], direction=query_msg_fields["direction"])

            if queryMsg.direction == 'l':
                ip = thisNode.getPrevIp()
                id = thisNode.getPrev()
            else:
                ip = thisNode.getNextIp()
                id = thisNode.getNext()


            # \add/edit current node's DHT
            requests.post(f"http://{ip}/propagate_query_2manager/",
                            json=queryMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
                            "msg": f"Forwarded query request to {id}"})


    @app.route('/propagate_query_ack/', methods=['POST'])
    def propagate_query_ack():
        ack_msg_fields = dict(request.get_json())
        #print("\x1b[33mAck Dict\x1b[0m:", ack_msg_fields)
        if thisNode.getAssignedId() == ack_msg_fields["sender_id"]:
            #print("\x1b[32mMessage dict:\x1b[0m", insert_msg_fields)
            msg_id = ack_msg_fields['message_id']
            #print("!!!!!!!!!!!!1ack_msg_filesd = ",ack_msg_fields)
            res = ack_msg_fields['ack_result']
            thisNode.setAck(msg_id, True)
            thisNode.setAckValue(msg_id, res)
            # set overlay response as done

            return json.dumps({"status": "Success", \
                            "msg": f"Query process finished"})
        else:
            #print("\x1b[35mAck Dict\x1b[0m:", ack_msg_fields)
            ackMsg = AcknowledgeMessage(ack_msg_fields)

            #insertMsg.update(thisNode.getAssignedId(), thisNode.getIp())
            # request on other node for add2overlay
            requests.post(f"http://{thisNode.getNextIp()}/propagate_query_ack/",\
                            json=ackMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
            "msg": f"Forwarded query acknowledge to {thisNode.getNext()}"})

    @app.route('/wait4query/<string:msg_id>', methods=['GET'])
    def wait4query(msg_id):
        '''
        Endpoint that waits for deletion
        '''
        while (not thisNode.getAck()[msg_id]):
            time.sleep(1)
            print(f"in wait with ack: {thisNode.getAck()}")
            pass

        return json.dumps({"status": "Success", "QueryId":msg_id, \
                "Query":thisNode.getAck()[msg_id], "queryValue": thisNode.getAckValue()[msg_id]})




    @app.route('/add2queryall',methods=['POST'])
    def add2queryall():
        queryall_msg_fields = dict(request.get_json())
        queryallMsg = QueryAllMessage(queryall_msg_fields)

        if thisNode.getAssignedId() == queryall_msg_fields["sender_id"]:
            # set overlay response as done
            thisNode.setOverlayResponses(queryall_msg_fields["message_id"], queryall_msg_fields["data"])
            #print(thisNode.getOverlayResponses())
            return json.dumps({"status": "Success", \
                            "msg": f"Query * finished"})
        else:
            queryallMsg.update(thisNode.getAssignedId(), thisNode.getDHT())
            # request on other node for add2overlay
            requests.post(f"http://{thisNode.getNextIp()}/add2queryall",\
                            json=queryallMsg.__dict__)
            # return success on caller
            return json.dumps({"status": "Success", \
                            "msg": f"Forwarded query * request to {thisNode.getNext()}"})


    @app.route('/wait4queryall/<string:msg_id>', methods=['GET'])
    def wait4queryall(msg_id):
        while (msg_id not in thisNode.getOverlayResponses()):
            time.sleep(1)
            #print(type(msg_id), msg_id)
            #print(thisNode.getOverlayResponses())
            pass
        return json.dumps({"status": "Success", "OverlayId":msg_id, "Overlay":thisNode.getOverlayResponses()[msg_id] })



    @app.route('/delete_all', methods=['GET'])
    def delete_all():
        '''
        deletes caller's whole DHT
        '''
        tmp = thisNode.getDHT()
        tmp.clear()
        return json.dumps({"status": 'Success', \
                            })
    @app.route('/get_DHT', methods=['GET'])
    def get_DHT():
        return json.dumps({"DHT":thisNode.getDHT()})

    # @app.route('/delete_from_repl_DHT/<string:id>/<string:n>', methods=['POST'])
    # def delete_from_repl_DHT(id, n):
    #     '''
    #     After a node is inserted into the Chord Network and replication is enabled
    #     n: appropriate number of loops
    #     id: caller's node id.
    #     '''
    #     # get overlay from message
    #     overlay = dict(request.get_json())
    #
    #     if len(overlay) != 2:
    #         # get current node's repl_DHT
    #
    #
    #         curr_repl_DHT = thisNode.getReplDHT()
    #         print("\x1b[33mOverlay\x1b[0m:", overlay)
    #         # find keys to delete from rpl_DHT
    #         next_caller_node = overlay[id]
    #         temp = next_caller_node
    #         print("n:", int(n))
    #         if int(n) == 2:
    #             flag_start = temp
    #         for i in range(int(n)-2):
    #             if i == int(n)-4:
    #                 flag_start = temp
    #             if i == 0 and int(n)==3:
    #                 flag_start = temp
    #             temp = overlay[temp]
    #
    #         flag_end = temp
    #
    #         if thisNode.get_n_replicas() == 2:
    #             flag_start = id
    #             flag_end = overlay[id]
    #
    #         length = (int(flag_end) - int(flag_start)) % 10
    #         keys = [(i+int(flag_start)) % 10 for i in range(1, length+1)]
    #
    #         # if int(n)==2:
    #             # keys = [temp]
    #         for key in keys:
    #             if str(key) in curr_repl_DHT:
    #                 curr_repl_DHT.pop(str(key))
    #         #print("temp type is", temp, type(temp))
    #         #print("curr repl dht is ", curr_repl_DHT)
    #         print("\x1b[35mThis node is:\x1b[0m", thisNode.getAssignedId())
    #         print("\x1b[35mEnter node:\x1b[0m", id)
    #         print("\x1b[32mCalculated keys:\x1b[0m", keys)
    #         print("\x1b[32mDHT keys:\x1b[0m", curr_repl_DHT.keys())
    #         #curr_repl_DHT.pop(str(temp)) #apo to temp 8eloume na paroume to DHT tou kai na kanoume
    #         # pop sto curr_replDHT ta keys tou dht tou temp
    #
    #     return json.dumps({"status":"Success"})

    @app.route('/delete_from_repl_DHT/<string:id>/<string:n>', methods=['POST'])
    def delete_from_repl_DHT(id, n):
        '''
        After a node is inserted into the Chord Network and replication is enabled
        previous nodes need to delete some keys from their replica DHT.
        Therefore newly inserted node calls delete_from_repl_DHT on some of its previous nodes
        n: appropriate number of loops
        id: caller's node id.
        '''
        # get overlay from message
        overlay = dict(request.get_json())

        # if the network consists of 2 nodes then do nothing
        if len(overlay) != 2:
            # get current node's repl_DHT
            curr_repl_DHT = thisNode.getReplDHT()

            # flag_end is the node whose DHT keys should be deleted
            # flag_start is flag_end's previous node
            # It is Initialized from the node that enters the network
            # n is the appropriate number of repetitions, considering id node as start
            temp = id
            flag_start = id
            for i in range(int(n)-1):
                temp = overlay[temp]
                if i == int(n)-3:
                    flag_start = temp

            flag_end = temp

            # find keys to delete from rpl_DHT
            length = (int(flag_end) - int(flag_start)) % 10
            keys = [(i+int(flag_start)) % 10 for i in range(1, length+1)]

            for key in keys:
                if str(key) in curr_repl_DHT:
                    curr_repl_DHT.pop(str(key))

            # print("\x1b[33mOverlay\x1b[0m:", overlay)
            #print("temp type is", temp, type(temp))
            #print("curr repl dht is ", curr_repl_DHT)
            print("\x1b[35mThis node is:\x1b[0m", thisNode.getAssignedId())
            print("\x1b[35mEnter node:\x1b[0m", id)
            print("\x1b[32mCalculated keys:\x1b[0m", keys)
            print("\x1b[32mDHT keys:\x1b[0m", curr_repl_DHT.keys())
            #apo to temp 8eloume na paroume to DHT tou kai na kanoume
            # pop sto curr_replDHT ta keys tou dht tou temp

        return json.dumps({"status":"Success"})

    @app.route('/insert_me_to_your_repl_DHT' ,methods=['POST'])
    def insert_me_to_your_repl_DHT():
        '''
        merges sent DHT to callee's repl_DHT
        '''
        # get inserted_DHT
        inserted_DHT = dict(request.get_json())
        # print("augaugaugaugauguagua", thisNode.getReplDHT(), inserted_DHT, merge_dict(thisNode.getReplDHT(), inserted_DHT) )
        thisNode.setReplDHT(merge_dict(thisNode.getReplDHT(), inserted_DHT))
        return json.dumps({"status": "Success"})

    @app.route('/insert_to_repl_DHT', methods=['POST'])
    def insert_to_repl_DHT():
        '''
        Inserts to repl DHT the DHT of the departee's next node
        '''
        # get dht from message
        inserted_DHT = dict(request.get_json())
        thisNode.setReplDHT(merge_dict(thisNode.getReplDHT(), inserted_DHT))
        return json.dumps({"status": "Success"})

    @app.route('/update/<string:departee_id>', methods=['GET'])
    def update(departee_id):
        '''
        Get the next next node's DHT
        '''
        print("\x1b[36mDepartee ID:\x1b[0m", departee_id)
        flag_next = thisNode.overlay_dict[departee_id]
        flag_prev = thisNode.reverse_overlay_dict[departee_id]
        thisNode.overlay_dict.pop(departee_id)
        thisNode.overlay_dict[flag_prev] = flag_next
        thisNode.reverse_overlay_dict.pop(departee_id)
        thisNode.reverse_overlay_dict[flag_next] = flag_prev

        return json.dumps({"status":"Success"})


    @app.route('/updateOverlay', methods=['GET'])
    def updateOverlay():
        res= thisNode.updateOverlay()
        return json.dumps({"status": res["status"]})

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
