from hashlib import sha1
import requests
import json
import random

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
    def __init__(self, ip, BOOTSTRAP_IP, isBootstrap=False, verbose=True):
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

    def clear(self):

        self.__init__(ip=self.ip, BOOTSTRAP_IP=self.BOOTSTRAP_IP,\
                isBootstrap=self.isBootstrap, verbose=False)

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

    def insertToDht(self, key, val):
        self.DHT[key] = val

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
        #ntf_next_req = ntf_next_req.json()
        # print("DHT:", ntf_next_req["DHT"])
        # self.DHT = ntf_next_req["DHT"]
        # print("DHT KEYS",self.DHT.keys())
        #print(ntf_next_req)

    def join(self):
        '''
        API request to join the P2P network.
        Request is sent to self.BOOTSTRAP_IP
        should set self.prev, self.next
        '''
        if self.isBootstrap:
            self.assigned_id = getId(self.ip)
            self.id_ip_dict[self.assigned_id] = self.ip

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
            self.assigned_id = join_req["assigned_position"]
            print("joined with assigned id", self.assigned_id, "prev id", \
                self.prev_id, "next id", self.next_id)

            self.notify_join_prev()
            self.notify_join_next()

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
                self.notify_depart_prev()
                self.notify_depart_next()
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
        raise NotImplementedError

    def query(self, key):
        '''
        API request the value that corresponds to a
        key stored in a node's hash table

        '''
        raise NotImplementedError
    def query_all(self):
        '''
        API request all <key, value> pairs in the DHT
        '''
        raise NotImplementedError
    def getNext(self):
        '''
        to get next node id
        '''
        return self.next_id

    def getPrev(self):
        '''
         get previous node id
        '''
        return self.prev_id
    def getAssignedId(self):
        '''
        returns assigned id
        '''
        return self.assigned_id

    def getDHT(self):
        '''
        get DHT keys from local Node
        '''
        return self.DHT
    def getOverlay(self):
        '''
        API request to get overlay of network's topology.
        '''
        raise NotImplementedError

class BootstrapNode(Node):
    def __init__(self, ip):
        super().__init__(ip, ip, True)
        self.id_ip_dict = {}

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

        prev_id = keys_in_dict[(self_index_in_dict -1)%len(keys_in_dict)]
        next_id = keys_in_dict[(self_index_in_dict +1)%len(keys_in_dict)]
        prev_ip = self.id_ip_dict[prev_id]
        next_ip = self.id_ip_dict[next_id]

        return joinee_id, prev_ip, next_ip

    def get_id_ip_dict(self):
        return self.id_ip_dict

if __name__== '__main__':
    print("testing node.py")
