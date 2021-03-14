class Message:
    def __init__(self, data_dict=None, msg_id=-1, sender_id=-1, sender_ip=-1, msg="", verbose=False):

        if data_dict == None:
            if verbose:
                print(f"Created message sent from id: {sender_id}, with id {msg_id}")

            self.message_id = msg_id
            self.sender_id = sender_id
            self.sender_ip = sender_ip
            self.msg = msg
            self.type = "Basic"
        else:
            self.setBasicData(data_dict)


    def getMsg(self):
        return self.msg

    def getSenderId(self):
        return self.sender_id

    def getMsgId(self):
        return self.message_id

    def getSenderIp(self):
        return self.sender_ip

    def getType(self):
        return self.type

    def setBasicData(self, data_dict):
        self.message_id = data_dict["message_id"]
        self.sender_id = data_dict["sender_id"]
        self.sender_ip = data_dict["sender_ip"]
        self.msg = data_dict["msg"]
        self.type = data_dict["type"]

class OverlayMessage(Message):
    def __init__(self, data_dict=None, msg_id=-1, sender_id=-1, sender_ip=-1, msg="", verbose=False):
        if data_dict == None:
            super().__init__(data_dict, msg_id, sender_id, msg, verbose)
            self.type = "Overlay"
            self.data = {sender_id: sender_ip}
        else:
            self.setBasicData(data_dict)
            self.data = data_dict["data"].copy()

    def update(self, current_id, current_ip):
        self.data[current_id] = current_ip

class QueryAllMessage(Message):
    def __init__(self, data_dict=None, msg_id=-1, sender_id=-1, sender_ip=-1, sender_DHT={}, msg="", verbose=False):
        if data_dict==None:
            super().__init__(data_dict, msg_id, sender_id, msg, verbose )
            self.type = "QueryAll"
            self.data = {sender_id: sender_DHT}
        else:
            self.setBasicData(data_dict)
            self.data = data_dict["data"].copy()

    def update(self, current_id, current_DHT):
        self.data[current_id] = current_DHT

class InsertionMessage(Message):
    def __init__(self, data_dict=None, msg_id=-1, sender_id=-1, \
                sender_ip=-1, msg="", verbose=False, key_data=None, val_data=None):
        if data_dict == None:
            super().__init__(data_dict, msg_id, sender_id, msg, verbose)
            self.type = "Insert"
            self.data = {key_data: val_data}
        else:
            self.setBasicData(data_dict)
            self.data = data_dict["data"].copy()


class DeletionMessage(Message):
    def __init__(self, data_dict=None, msg_id=-1, sender_id=-1, \
                sender_ip=-1, msg="", verbose=False, key_data=None):
        if data_dict == None:
            super().__init__(data_dict, msg_id, sender_id, msg, verbose)
            self.type = "Delete"
            self.data = key_data
        else:
            self.setBasicData(data_dict)
            self.data = data_dict["data"]

class QueryMessage(Message):
    def __init__(self, data_dict=None, msg_id=-1, sender_id=-1, \
                sender_ip=-1, msg="", verbose=False, key_data=None):
        if data_dict == None:
            super().__init__(data_dict, msg_id, sender_id, msg, verbose)
            self.type = "Query"
            self.data = key_data
            self.ack_result = 'dummy'
        else:
            self.setBasicData(data_dict)
            self.data = data_dict["data"]
            self.ack_result = 'dummy'

class AcknowledgeMessage(Message):
    '''
    Used for acknowledging insertion,deletion queries and (key, val) queries.
    '''
    def __init__(self, data_dict=None, msg_id=-1, sender_id=-1, \
                sender_ip=-1, msg="", verbose=False, ackType="UNK", ack_result=None):
            if data_dict == None:
                super().__init__(data_dict, msg_id, sender_id, msg, verbose)
                self.type = ackType
                #self.ack_type = ackType
                # if self.ack_type == "Query":
                #     self.ack_result = ack_result
            else:
                self.setBasicData(data_dict)
                #self.ack_type = data_dict["type"]
                #self.type = "Ack"

                if self.type == "Query":
                    self.ack_result = data_dict["ack_result"]
