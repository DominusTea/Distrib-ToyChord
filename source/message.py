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
