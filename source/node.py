from hashlib import sha1
'''
Contains code for node class
implementing basic insertion, query operations
to the network. It handles graceful join and departure
'''

class Node:
    '''
    orismoi
    '''
    def __init__(self, ip, isBootstrap=False, BOOTSTRAP_IP):
        '''initializations'''
        self.ip=ip
        self.isBootstrap = isBootstrap
        self.BOOTSTRAP_IP = BOOTSTRAP_IP
        self.id = sha1(self.ip.encode()).hexdigest() #hash in hexadecimal
        self.DHT = {} # hash table for this node
        # self.id =  SHA.new((str(self.ip)+str(self.previousHash_hex)+str(self.nonce)).encode())
    def join(self):
        '''
        API request to join the P2P network.
        Request is sent to self.BOOTSTRAP_IP
        should set self.prev, self.next
        '''

        raise NotImplementedError
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
        API request to get next node
        '''
        raise NotImplementedError
    def getPrev(self):
        '''
        API request to get previous node
        '''
        raise NotImplementedError

class BootstrapNode(Node):
    def __init__(self, ip):
        super().__init__(ip, isBootstrap=True)

if __name__== '__main__':
    print("testing node.py")
