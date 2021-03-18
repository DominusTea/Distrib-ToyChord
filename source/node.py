from hashlib import sha1
import requests
import json
import random
from source.message import *
from source.lib import *

'''
Contains code for node class
implementing basic insertion, query operations
to the network. It handles graceful join and departure
'''
def getId(ip):
    return int(sha1(ip.encode()).hexdigest(),16)%10


class Node:
    '''
    orismoi
    '''
    def __init__(self, ip, BOOTSTRAP_IP, n_replicas=1, isBootstrap=False, verbose=True):
        '''initializations'''
        if(verbose):
            print(f"Created node with ip: {ip}, bootstrap ip: {BOOTSTRAP_IP}, isBootstrap={isBootstrap}")
        self.ip=ip
        self.isBootstrap = isBootstrap
        self.BOOTSTRAP_IP = BOOTSTRAP_IP
        #self.id = None #sha1(self.ip.encode()).hexdigest() #hash in hexadecimal
        self.assigned_id = None #assigned Chord position
        self.DHT = {} # hash table for this node
        self.prev_ip = None
        self.next_ip = None
        self.prev_id = None
        self.next_id = None
        self.msg_id = 0
        self.responses = {}
        self.ack = {}
        self.ack_value = {}
        self.n_replicas = n_replicas
        if self.n_replicas > 1:
            self.repl_DHT = {} # key: hashkey, value: val (dummy). Data replicated from other nodes.
            self.replicas = {} # key: id, value: ip for the node's replicas.
            self.prev_nodes = {} #key: id, value ip for the node's previous nodes

    def clear(self):

        self.__init__(ip=self.ip, BOOTSTRAP_IP=self.BOOTSTRAP_IP, \
            n_replicas=self.n_replicas, isBootstrap=self.isBootstrap, verbose=False)

    def set_prev(self, ip, id):
        '''
        Update node's previous node with input ip
        '''
        self.prev_ip = ip
        self.prev_id = id

    def set_next(self, ip, id):
        '''
        Update node's next node with input ip
        '''
        self.next_ip = ip
        self.next_id = id

    def setDHT(self,dht_dict):
        self.DHT = dht_dict.copy()

    def setReplDHT(self, repl_dht_dict):
        self.repl_DHT = repl_dht_dict.copy()

    def setAck(self, msg_id, msg_val):
        self.ack[msg_id] = msg_val

    def setAckValue(self, msg_id, msg_val):
        self.ack_value[msg_id] = msg_val

    def setOverlayResponses(self, msg_id, msg_val):
        print("a:", msg_id)
        print("type of msg_id:", type(msg_id))
        if type(msg_id)==str:
            self.responses[msg_id] = msg_val
            print("dict:", self.responses)
        else:
            print("Set Overlay Response ERRROR")

    def insertToDht(self, key, hash, val):
        self.DHT[hash][key] = val

    def deleteFromDht(self, key, hash):
        if key in self.DHT[hash]:
            self.DHT[hash].pop(key)

    def queryFromDht(self, key, hash):
        if key in self.DHT[hash]:
            res = self.DHT[hash][key]
            # print("\x1b[32mDHT: \x1b[0m", self.DHT)
            # print("\x1b[32mResult: \x1b[0m", res)
        else:
            res ="Not found"
        return res

    def notify_join_prev(self):
        ntf_prev_req = (requests.get("http://"+self.prev_ip+f"/accept_join_next/{self.ip}/{self.assigned_id}")).json()

    def notify_join_next(self):
        ntf_next_req = (requests.get("http://"+self.next_ip+f"/accept_join_prev/{self.ip}/{self.assigned_id}")).json()
        # this should be of the form status. , list of all keys in next's DHT
        self.DHT = ntf_next_req["DHT"]

    def notify_depart_prev(self):
        ntf_prev_req = (requests.get("http://"+self.prev_ip+f"/accept_depart_next/{self.next_ip}/{self.next_id}")).json()

    def notify_depart_next(self):
        #print("DHT", self.DHT)
        departee_dict = json.dumps(self.DHT)
        #print("JSON:", departee_dict)
        ntf_next_req = (requests.post("http://"+self.next_ip+f"/accept_depart_prev/{self.prev_ip}/{self.prev_id}",\
                        json=self.DHT)).json()

    def notify_repl_join_next(self):
        '''
        notify the k-1 next neighbours to get the appropriate keys
        If not using replicas, this function doesn't do anything
        '''
        print("\x1b[31mNext Nodes:\x1b[0m", self.replicas.keys())
        if self.n_replicas > 1:
            # this is equivalent to replicas!={}
            # that is, the Network doesnt use replicas
            for repl_ip in self.replicas.values():
                # get replicas DHT
                replicas_DHT = (requests.get("http://"+repl_ip+"/get_DHT")).json()["DHT"]
                # and merge it with current node's repl_DHT
                self.repl_DHT = merge_dict(self.repl_DHT, replicas_DHT)

    def notify_repl_join_prev(self, overlay):
        '''
        notify the k-1 prev neighbours to get the appropriate keys.
        If not using replicas, this function doesn't do anything.
        '''
        print("\x1b[31mPrev Nodes:\x1b[0m", self.prev_nodes.keys())
        if self.n_replicas > 1:
            counter = list(range(self.n_replicas, 0, -1))
            for i, repl_ip in enumerate(self.prev_nodes.values()):
                # notify previous nodes to delete appropriate keys from their repl_DHT
                # since other nodes replicate them now (after a join)
                if len(overlay) > self.n_replicas:
                    req = (requests.post("http://"+repl_ip+f"/delete_from_repl_DHT/{self.assigned_id}/{counter[i]}", json=overlay)).json()
                add = (requests.post("http://"+repl_ip+f"/insert_me_to_your_repl_DHT", json=self.DHT)).json()



    def find_DHT_part(self, n, overlay):
        temp = str(self.assigned_id)
        flag_start = temp
        for i in range(int(n)-1):
            temp = overlay[temp]
            if i == int(n)-3:
                flag_start = temp
        flag_end = temp
        length = (int(flag_end) - int(flag_start)) % 10
        keys = [(i+int(flag_start)) % 10 for i in range(1, length+1)]
        DHT = {}
        print("\x1b[36mRepl DHT\x1b[0m", self.repl_DHT.keys())
        for key in keys:
            DHT[str(key)] = self.repl_DHT[str(key)]
        return DHT

    def notify_repl_depart_prev(self, overlay):
        if self.n_replicas > 1:
            counter = list(range(self.n_replicas, 0, -1))
            for i, repl_ip in enumerate(self.prev_nodes.values()):
                # notify previous nodes to delete appropriate keys from their repl_DHT
                # since other nodes replicate them now (after a join)
                DHT = self.find_DHT_part(counter[i], overlay)
                print("\x1b[32mDHT keys to be inserted\x1b[0m", DHT.keys())

                req = (requests.post("http://"+repl_ip+f"/insert_to_repl_DHT", json=DHT)).json()
                #add = (requests.post("http://"+repl_ip+f"/insert_me_to_your_repl_DHT", json=self.DHT)).json()




    def join(self):
        '''
        API request to join the P2P network.
        Request is sent to self.BOOTSTRAP_IP
        should set self.prev, self.next
        '''
        if self.isBootstrap:
            self.assigned_id = getId(self.ip)
            self.id_ip_dict[self.assigned_id] = self.ip
            self.overlay_dict= {str(self.assigned_id):None}
            self.reverse_overlay_dict = {str(self.assigned_id):None}

            print("joined with assigned id", self.assigned_id)
            # load data from local directory. ONLY FOR TESTING DELETE LATER
            print("http://"+self.ip+"/load_data_from_file")
            requests.get("http://"+self.ip+"/load_data_from_file")

            return {"text": "This is the bootstrap node", \
                    "assigned_position": getId(self.ip),\
                    "prev": self.prev_ip, \
                    "next": self.next_ip, \
                    "status": "Success" }
        else:
            join_req = (requests.get("http://"+self.BOOTSTRAP_IP+f"/check_join/{self.ip}")).json()
            self.prev_ip = join_req["prev_ip"]
            self.next_ip = join_req["next_ip"]
            self.prev_id = getId(join_req["prev_ip"])
            self.next_id = getId(join_req["next_ip"])
            self.replicas = join_req["replicas"]
            self.prev_nodes = join_req["prev_nodes"]
            self.assigned_id = join_req["assigned_position"]
            overlay = join_req["overlay"]
            print("joined with assigned id", self.assigned_id, "prev id", \
                self.prev_id, "next id", self.next_id)

            # notify previous and next node. Get corresponding DHTs.
            self.notify_join_prev()
            self.notify_join_next()

            # notify previous and next to refresh their repl_DHT and update current node's repl_DHT
            self.notify_repl_join_prev(overlay)
            self.notify_repl_join_next()



            return {"status": "Success", \
                    "text": f"Joined with prev: {self.prev_ip}, next: {self.next_ip}", \
                    "prev": self.prev_ip, \
                    "next": self.next_ip, \
                    "assigned_position": self.assigned_id
            }


    def depart(self):
        '''
        API request to gracefully depart from the P2P Network.
        Request is sent to self.BOOTSTRAP_IP
        should update prev, next
        '''
        if self.isBootstrap:
            return {"text": "This is Bootstrap node. Undefined Behavour",\
                    "status": "Success"}
        else:
            depart_req = (requests.get("http://"+self.BOOTSTRAP_IP+f"/check_depart/{self.assigned_id}")).json()
            if depart_req["status"] == "Success":
                # must notify neighbours about departure

                self.prev_nodes = depart_req["prev_nodes"]
                self.overlay = depart_req["overlay"]

                self.notify_depart_prev()
                self.notify_depart_next()

                self.notify_repl_depart_prev(self.overlay)


                print("\x1b[36mID:\x1b[0m", self.assigned_id)
                req = (requests.get("http://"+self.BOOTSTRAP_IP+f"/update/{str(self.assigned_id)}")).json()
                self.clear()
                return {"status": "Success", \
                    "text": f"Depart from P2P network with id {self.assigned_id}, prev {self.prev_id} and next {self.next_id}."}
            else:
                print(f"\x1b[31mError at depart procedure for id {self.assigned_id}\x1b[0m")

    def insert(self, key, value):
        '''
        API request to insert value. If it already exists
        then the value is updated instead.
        '''
        hashkey = str(getId(key))
        if hashkey in self.getDHT().keys():
            self.insertToDht(key, hashkey, value)
            return {"status": "Success", \
                   "text": f"Successfuly added {key}, {value} in node {self.assigned_id}"}

        else:
            msg_id = self.getMsgId()
            self.setAck(msg_id, False)
            print("First Node:", self.getAck())
            insert_msg = InsertionMessage(msg_id=msg_id, sender_id=self.assigned_id, sender_ip=self.ip, msg="", key_data=key, val_data=value)
            # propagate insertion to next node
            insert_req = (requests.post(f"http://{self.next_ip}/propagate_insert/", json=insert_msg.__dict__)).json()
            # wait for response at wait4insert endpoint.
            wait_req = (requests.get("http://"+self.ip+f"/wait4insert/{msg_id}")).json()

        return wait_req

    def delete(self, key):
        '''
        API request to delete pair with given key. If it doesnt exists
        then nothing happens
        '''
        hashkey = str(getId(key))
        if hashkey in self.getDHT().keys():
            self.deleteFromDht(key, hashkey)
            return {"status": "Success", \
                   "text": f"Successfuly removed pair with key: {key} from node: {self.assigned_id}"}

        else:
            # current node not responsible for hashKey. Construct Delete Message
            msg_id = self.getMsgId()
            self.setAck(msg_id, False)
            print("First Node:", self.getAck())
            delete_msg = DeletionMessage(msg_id=msg_id, sender_id=self.assigned_id, sender_ip=self.ip, msg="", key_data=key)
            # propagate deletion to next node
            deletion_req = (requests.post(f"http://{self.next_ip}/propagate_delete/", json=delete_msg.__dict__)).json()
            # wait for response at wait4delete route
            wait_req = (requests.get("http://"+self.ip+f"/wait4delete/{msg_id}")).json()

        return wait_req

    def query(self, key):
        '''
        API request the value that corresponds to a
        key stored in a node's hash table

        '''
        hashkey = str(getId(key))
        if hashkey in self.getDHT().keys():
            queryVal = self.queryFromDht(key, hashkey)
            return {"status": "Success", \
                   "text": f"Successful query for pair with key: {key} from node: {self.assigned_id}. Result: {queryVal}", \
                   "queryValue": {queryVal}}

        else:
            # current node not responsible for hashKey. Construct Delete Message
            msg_id = self.getMsgId()
            # set ack to False, since node has not received ack for request
            self.setAck(msg_id, False)
            # set ackvalue to None, since node has not received ack for request
            self.setAckValue(msg_id, None)
            query_msg = QueryMessage(msg_id=msg_id, sender_id=self.assigned_id, sender_ip=self.ip, msg="", key_data=key)
            # propagate query to next node
            query_req = (requests.post(f"http://{self.next_ip}/propagate_query/", json=query_msg.__dict__)).json()
            # wait for response at wait4query route
            wait_req = (requests.get("http://"+self.ip+f"/wait4query/{msg_id}")).json()

        return wait_req

    def query_all(self):
        '''
        API request all <key, value> pairs in the P2P network (for every node)
        '''
        msg_id = self.getMsgId()

        queryall_msg = QueryAllMessage(msg_id=msg_id, sender_id=self.assigned_id, \
                            sender_DHT=self.DHT, msg="")
        # begin asking for query * from next ip
        queryall_req = (requests.post(f"http://{self.next_ip}/add2queryall", json=queryall_msg.__dict__)).json()
        # wait for response at wait4queryall route
        queryall_response = (requests.get(f"http://{self.ip}/wait4queryall/{msg_id}")).json()

        return queryall_response


    def getBootstrap(self):
        return self.isBootstrap

    def get_n_replicas(self):
        '''
        returns number of replicas
        '''
        return self.n_replicas

    def getNext(self):
        '''
        get next node's id
        '''
        return self.next_id
    def getNextIp(self):
        '''
        get next node's ip
        '''
        return self.next_ip
    def getPrev(self):
        '''
        get previous node's id
        '''
        return self.prev_id

    def getPrevIp(self):
        '''
        get prev node's ip
        '''
        return self.prev_ip

    def getAssignedId(self):
        '''
        returns node's assigned id
        '''
        return self.assigned_id
    def getIp(self):
        '''
        returns node's ip
        '''
        return self.ip

    def getDHT(self):
        '''
        get DHT  from local Node
        '''
        return self.DHT

    def getReplDHT(self):
        '''
        get Replica DHT from local Node
        '''
        return self.repl_DHT

    def getTotalDHT(self):
        '''
        Returns DHT merged with replica DHT.
        '''
        return merge_dict(self.DHT, self.repl_DHT)

    def getMsgId(self):
        '''
        Returns unique message id concatenated with NodeId.
        The Id is unique globally.

        '''
        print("before: ", self.msg_id)
        self.msg_id += 1
        print("after: ", self.msg_id)
        return  str(self.assigned_id) + "_" + str(self.msg_id)

    def getOverlay(self):
        '''
        API request to get overlay of network's topology.
        '''
        msg_id = self.getMsgId()
        overlay_msg = OverlayMessage(msg_id=msg_id, sender_id=self.assigned_id, \
                            sender_ip=self.ip, msg="")
        # begin asking for overlay from next ip
        overlay_req = (requests.post(f"http://{self.next_ip}/add2overlay/", json=overlay_msg.__dict__)).json()
        # wait for response at wait4overlay route
        overlay_response = (requests.get(f"http://{self.ip}/wait4overlay/{self.assigned_id}/{msg_id}")).json()

        return overlay_response

    def getOverlayResponses(self):
        return self.responses

    def getAck(self):
        return self.ack

    def getAckValue(self):
        return self.ack_value

class BootstrapNode(Node):
    def __init__(self, ip, n_replicas):
        super().__init__(ip, ip, n_replicas, True)
        self.id_ip_dict = {} # key: int, value: str
        self.overlay_dict = {} # key: node_id (str), value: node's next id (str). Following "next" order
        self.reverse_overlay_dict={} # key: node_id, value: node's prev id. Following "prev" order
        for i in range(10):
            self.DHT[str(i)] = {}

    def check_join(self, joinee_ip):
        '''
        returns assigned position, prev_ip, next_ip,
        '''

        joinee_id = getId(joinee_ip)
        if joinee_id in self.id_ip_dict:
            joinee_id = \
                random.choice(list({0,1,2,3,4,5,6,7,8,9} - set(self.id_ip_dict.keys())))

        self.id_ip_dict[joinee_id] = joinee_ip

        keys_in_dict = sorted(list(self.id_ip_dict.keys()))
        self_index_in_dict = keys_in_dict.index(joinee_id)
        # get previous nodes ips, ids
        prev_id = keys_in_dict[(self_index_in_dict -1)%len(keys_in_dict)]
        next_id = keys_in_dict[(self_index_in_dict +1)%len(keys_in_dict)]
        prev_ip = self.id_ip_dict[prev_id]
        next_ip = self.id_ip_dict[next_id]
        # update overlay dict
        self.overlay_dict[str(joinee_id)] = str(next_id)
        self.reverse_overlay_dict[str(joinee_id)] = str(prev_id)

        if len(self.overlay_dict) == 2:
            self.overlay_dict[str(next_id)] = str(joinee_id)
            self.reverse_overlay_dict[str(prev_id)] = str(joinee_id)
        else:
            self.overlay_dict[str(prev_id)] = str(joinee_id)
            self.reverse_overlay_dict[str(next_id)] = str(joinee_id)

        print("\x1b[33mOverlay\x1b[0m:", self.overlay_dict)
        print("\x1b[33mId-Ip\x1b[0m:", self.id_ip_dict)
        print("\x1b[33mJoinee\x1b[0m:", joinee_id, type(joinee_id))


        # if Network uses replicas:
        if self.n_replicas > 1:
            # find n_replicas-1 next consequent nodes ( to be replicated by callee node)
            n_next_nodes = get_n_consequent(self.overlay_dict, self.id_ip_dict,\
                                        self.n_replicas-1, str(joinee_id))
            # find n_replicas-1 prev consequent nodes ( that may have to update their repl_DHT)
            n_prev_nodes = get_n_consequent(self.reverse_overlay_dict, self.id_ip_dict, \
                                        self.n_replicas-1, str(joinee_id))

        else:
            n_next_nodes = {}
            n_prev_nodes = {}

        return joinee_id, prev_ip, next_ip, n_next_nodes, n_prev_nodes, self.overlay_dict


    def check_depart(self, departee_id):
        # if Network uses replicas:
        if self.n_replicas > 1:
            # find n_replicas-1 prev consequent nodes ( that may have to update their repl_DHT)
            n_prev_nodes = get_n_consequent(self.reverse_overlay_dict, self.id_ip_dict, \
                                        self.n_replicas-1, departee_id)

        else:
            n_next_nodes = {}
            n_prev_nodes = {}

        self.id_ip_dict.pop(int(departee_id))
        return n_prev_nodes, self.overlay_dict



    def get_id_ip_dict(self):
        return self.id_ip_dict

if __name__== '__main__':
    print("testing node.py")
