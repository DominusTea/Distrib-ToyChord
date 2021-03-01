from hashlib import sha1
import requests

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
    def __init__(self, ip, BOOTSTRAP_IP, isBootstrap=False):
        '''initializations'''
        self.ip=ip
        self.isBootstrap = isBootstrap
        self.BOOTSTRAP_IP = BOOTSTRAP_IP
        self.id = None #sha1(self.ip.encode()).hexdigest() #hash in hexadecimal
        self.assigned_id = None #assigned Chord position
        self.DHT = {} # hash table for this node
        self.prev_ip = None
        self.next_ip = None
        self.prev_id = None
        self.next_id = None

    def set_prev(self, ip):
        '''
        Update node's previous node with input ip
        '''
        self.prev_ip = ip
        self.prev_id = getId(ip)

    def set_next(self, ip):
        '''
        Update node's next node with input ip
        '''
        self.next_ip = ip
        self.next_id = getId(ip)

    def notify_prev(self):
        ntf_prev_req = json.loads(requests.get("https://"+self.prev_ip+f"/accept_next/{self.ip}"))

    def notify_next(self):
        ntf_next_req = json.loads(requests.get("https://"+self.next_ip+f"/accept_prev/{self.ip}"))
        # this should be of the form status. , list of all keys in next's DHT
        self.DHT = ntf_next_req["DHT"]



    def join(self):
        '''
        API request to join the P2P network.
        Request is sent to self.BOOTSTRAP_IP
        should set self.prev, self.next
        '''
        if self.isBootstrap:
            return {text: "This is the bootstrap node", \
                    assigned_position: int(self.id,16)%10,\
                    prev: self.prev_ip, \
                    next: self.next_ip, \
                    status: "Success" }
        else:
            join_req = json.loads(requests.get("https://"+self.BOOTSTRAP_IP+"/check_join"))
            self.prev_ip = join_req["prev_ip"]
            self.next_ip = join_req["next_ip"]
            self.prev_id = getId(join_req["prev_ip"])
            self.next_id = getId(join_req["next_ip"])
            self.assigned_id = join_req["assigned_position"]

            notify_prev()
            notify_next()

            return {status: "Success", \
                    text: f"Joined with prev: {self.prev}, next: {self.next}", \
                    prev: self.prev, \
                    next: self.next, \
                    assigned_position: self.assigned_id
            }


    def depart(self):
        '''
        API request to gracefully depart from the P2P Network.
        Request is sent to self.BOOTSTRAP_IP
        should update prev, next
        '''
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
        to get next node
        '''
        raise NotImplementedError
    def getPrev(self):
        '''
         get previous node
        '''
        raise NotImplementedError
    def getDHTK(self):
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
        super().__init__(ip, isBootstrap=True)

if __name__== '__main__':
    print("testing node.py")
