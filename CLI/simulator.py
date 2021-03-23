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
    return input
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
            line = line.strip("\n")
            if mode=="requests":
                l = line.split(" ")
                query_type = l[0][:-1]
                if query_type == "query":
                    # query request
                    song = ' '.join(l[1:])
                    req_str = (query_type , song )
                    self.req_lst.append(req_str)
                elif query_type == "insert":
                    # insert request
                    value = l[-1]
                    song = ' '.join(l[1:-1])[:-1]
                    req_str = (query_type ,  song  ,  value)
                    self.req_lst.append(req_str)
                else:
                    raise InputError(f"input file contains illegal line: {i}")

            elif mode=="inserts":
                l = line.split(" ")
                print("Line", line)
                value = l[-1]
                song = ' '.join(l[0:-1])[:-1]
                req_str = ("insert" , song ,  value)
                self.req_lst.append(req_str)

            elif mode=="queries":
                req_str = ("query",  line)
                self.req_lst.append(req_str)

            else:
                raise ValueError("mode should be one of [ requests | inserts | queries ]")

    def simulate(self, output_dir=None):
        '''
        Randomly chooses one Chord node for each request and sends it to be executed by it.
        '''
        # start counting time
        start_time = time.time()
        if output_dir is not None:
            simu_file = open(output_dir, "w+")
        for req in self.req_lst:

            # randomly select one node
            node_id = random.choice(list(self.id_ip_dict.keys()))
            # and get its ip
            node_ip = self.id_ip_dict[node_id]
            # req = req.split(" ")
            #mode = req.split(" ")[0]
            # req = req.split(" ")
            mode = req[0]
            # song = ' '.join(req[1:])
            print("Req:", req)
            if mode == "delete":

                res = requests.post(f"http://{node_ip}/delete", \
                        json={"key_data":req[1]})

            elif mode == "insert":

                res = requests.post(f"http://{node_ip}/insert", \
                            json={"key_data":req[1], "val_data":req[2]})
            elif mode == "query":
                # print(f"query for {req}")
                res = requests.post(f"http://{node_ip}/query", \
                            json={"key_data":req[1]})
            else:
                raise RuntimeError("illegal request", req)
            if output_dir is not None:
                simu_file.write(str(res.json()))
                simu_file.write("\n")


        end_time = time.time()
        duration = end_time - start_time
        average_throughput = len(self.req_lst)/duration
        return average_throughput, len(self.req_lst)
