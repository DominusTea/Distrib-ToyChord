import os

from flask import Flask
from source.node import Node, getId

#router stuff
import requests
import json

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
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    thisNode =Node(app.THIS_IP, app.BOOTSTRAP_IP, app.isBootstrap)
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'+str(app.config["BOOTSTRAP_IP"])

    @app.route('/join/<string:joinee_ip>', methods=['GET'])
    def join(joinee_ip):
        join_req = thisNode.join()
        # result should have :
        # text -> successfuly joined the network. Assigned position ???
        # assigned_position -> ???
        # prev [ip]
        # next [ip]
        # status -> error or success
        if join_req.status == 'error':
            print("error in joining")
        else:
            # notifiy neighbours about joining
            # previous must know that the joinee is his next
            prev_update_req = requests.get("https://")

            # next must know that the joinee is his prev and give him some of his data

            return join_req


    @app.route('/accept_next/<string:next_ip>')
    def accept_next(next_ip):
        thisNode.set_next(next_ip)
        return json.dumps({"status": "Success"
        })
    @app.route('/accept_prev/<string:prev_ip>')
    def accept_prev(prev_ip):
        '''
        Input: previous node's ip
        route is accessed from current Node (middle)
        Route belongs to  next Node (right)
        updates next's DHT
        returns current's DHT
        '''
        # thisNode.set_prev(prev_ip)
        # nodesKeys = thisNode.getDHT().keys()
        # prevKeys = [thisNode.DHT[i] for i in nodesKeys if i <= getId(prev_ip) ]

        thisNode.set_prev(prev_ip)
        nodesDHT = thisNode.getDHT()
        # get current's (middle) DHT
        newDHT = {i:nodesDHT[i] for i in nodesDHT.keys() if i <= getId(prev_ip)}
        # update next's (right) DHT
        for i in newDHT.keys():
            nodesDHT.pop(i)

        return json.dumps({"status": "Success",
                            "DHT" : newDHT,
        })


    return app
