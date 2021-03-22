# for requesting
import requests
import random
import threading
# for timing
import time

def autakia(input):
    '''
    Inserts '"' at the start and the end of a sting
    '''
    return '"' + input + '"'

class Simulator:
    '''
    Simulator class that emits API requests to backend
    '''
    def __init__(self, id_ip_dict):
        self.id_ip_dict = id_ip_dict
        self.req_lst = []

    def insert_requests(self, filepath="", mode="requests"):
        '''
        prepares request for our cli api
        and stores them for the simulation.
        '''
        f = open(filepath, "r")
        for i, line in enumerate(f):
            line = line[0:-2]
            if mode=="requests":
                l = line.split(",")
                if len(l) == 2:
                    # query request
                    req_str = l[0] + ' ' + autakia(l[1])
                    self.req_lst.append(req_str)
                elif len(l) == 3:
                    req_str = l[0] + ' ' + autakia(l[1]) + ' '+ l[2]
                    self.req_lst.append(req_str)
                else:
                    raise InputError(f"input file contains illegal line: {i}")

            elif mode=="inserts":
                l = line.split(",")
                if len(l) == 2:
                    req_str = "insert " + autakia(l[0]) + ' '+ l[1]
                    self.req_lst.append(req_str)
                else:
                    raise InputError(f"input file contains illegal line: {i}")

            elif mode=="queries":
                l = line.split(",")
                if len(l) == 1:
                    req_str = "query " + autakia(l[0])
                    self.req_lst.append(req_str)
                else:
                    raise InputError(f"input file contains illegal line: {i}")
            else:
                raise ValueError("mode should be one of [ requests | inserts | queries ]")

    def simulate(self):
        '''
        Randomly chooses one Chord node for each request and sends it to be executed by it.
        '''
        # start counting time
        start_time = time.time()
        for req in self.req_lst:
            # randomly select one node
            node_id = random.choice(list(self.id_ip_dict.keys()))
            # and get its ip
            node_ip = self.id_ip_dict[node_id]
            mode = req.split(" ")[0]
            if mode == "delete":

                res = requests.post(f"http://{node_ip}/delete", \
                        json={"key_data":req[1]})

            elif mode == "insert":
                res = requests.post(f"http://{node_ip}/insert", \
                            json={"key_data":req[1], "val_data":req[2]})
            elif mode == "query":
                res = requests.post(f"http://{node_ip}/query", \
                            json={"key_data":req[1]})
            else:
                raise RuntimeError("illegal request", req)
        end_time = time.time()
        duration = end_time - start_time
        average_time = duration/len(self.req_lst)
        return average_time, len(self.req_lst)
