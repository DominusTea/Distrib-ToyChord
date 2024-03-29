import click
from click_repl import register_repl
import json
# for requesting
import requests
# for simulating
import simulator
import numpy as np

@click.group()
def cli():
    pass

@cli.command()
def help():
    click.echo("-----------Available Commands------------")
    click.echo("join : Joins the P2P distributed system")
    click.echo("depart : Exits the P2P distributed system")
    click.echo("insert -key -value : Inserts (key,value) pair into the P2P network")
    click.echo("delete -key : Deletes (key,value) pair from the P2P network")
    click.echo("query -key : Queries the P2P system where the key is stored")
    click.echo("overlay : Returns the topology of the network")
    click.echo("--------------------------------------\n")

@cli.command()
def hello():
    click.echo("Hello world!")

@cli.command()
@click.argument('ip')
@click.argument('boot_ip')
@click.argument('port')

def give_credentials(ip, boot_ip, port):
    global THIS_IP, BOOTSTRAP_IP, THIS_PORT, hasLoggedIn
    THIS_IP = ip
    BOOTSTRAP_IP = boot_ip
    THIS_PORT = port
    hasLoggedIn = True
    click.echo(f"Set Ip to {THIS_IP}")


@cli.command()
def overlay():
    if hasLoggedIn:
        click.echo(f"Attempting to get Network's overlay.")
        res = requests.get(f"http://{THIS_IP}:{THIS_PORT}/overlay")
        click.echo("Successfully found Network's overlay")
        click.echo(f"Overlay: {res.json()}")

    else:
        click.echo(f"Must login first (using give_credentials command)")

@cli.command()
@click.option(  '-a', \
                '--all', \
                default=False, \
                is_flag=True)
def join(all):
    global hasJoined
    if hasLoggedIn:
        if not all:
            hasJoined = True
            click.echo(f"Attempting to join ToyChord P2P Network with ip = {THIS_IP}, port={THIS_PORT}, on bootstrap = {BOOTSTRAP_IP}")
            res = (requests.get(f"http://{THIS_IP}:{THIS_PORT}/join")).json()
            click.echo(f"Successfully joined with id {res['assigned_position']}")
        else:
            boot_ip = "192.168.1.1:5000"
            # joins all nodes based on credentials given
            for i in range(1, 6):
                tmp_ip="192.168.1."+str(i)
                tmp_port="5000"
                click.echo(f"Attempting to join ToyChord P2P Network with ip = {tmp_ip}, port={tmp_port}, on bootstrap = {BOOTSTRAP_IP}")
                res = (requests.get(f"http://{tmp_ip}:{tmp_port}/join")).json()
                click.echo(f"Successfully joined with id {res['assigned_position']}")
                tmp_port="5001"
                click.echo(f"Attempting to join ToyChord P2P Network with ip = {tmp_ip}, port={tmp_port}, on bootstrap = {BOOTSTRAP_IP}")
                res = (requests.get(f"http://{tmp_ip}:{tmp_port}/join")).json()
                click.echo(f"Successfully joined with id {res['assigned_position']}")
    else:
        click.echo(f"Must login first (using give_credentials command)")

@cli.command()
def depart():
    global hasJoined
    if hasLoggedIn and hasJoined:
        hasJoined=False
        click.echo(f"Attempting to depart from ToyChrod P2P Network")
        res = requests.get(f"http://{THIS_IP}:{THIS_PORT}/depart")
    else:
        click.echo(f"Must login first (using give_credentials command) and join")
@cli.command()
def print_all():
    if hasLoggedIn:
        click.echo(f"Local node running on ip{THIS_IP}:{THIS_PORT} has DHT:")
        res = requests.get(f"http://{THIS_IP}:{THIS_PORT}/print_all")
        click.echo(res.json())
    else:
        click.echo(f"Must login first (using give_credentials command)")

@cli.command()
@click.argument('key')
@click.argument('value')
def insert(key, value):
    if hasLoggedIn:
        click.echo(f"Attempting to insert ({key}, {value}) into the ToyChrod Network")
        res = requests.post(f"http://{THIS_IP}:{THIS_PORT}/insert", \
                    json={"key_data":key, "val_data":value})
        click.echo(res.json())
    else:
        click.echo(f"Must login first (using give_credentials command)")

@cli.command()
@click.argument('key')
def delete(key):
    if hasLoggedIn:
        click.echo(f"Attempting to delete {key} from the ToyChrod Network")
        res = requests.post(f"http://{THIS_IP}:{THIS_PORT}/delete", \
                    json={"key_data":key})
        click.echo(res.json())
    else:
        click.echo(f"Must login first (using give_credentials command)")

@cli.command()
@click.argument('key')
def query(key):
    if hasLoggedIn:

        if key=="*":
            click.echo(f"Attempting to query all (*) from the ToyChrod Network")
            res = requests.get(f"http://{THIS_IP}:{THIS_PORT}/queryall")

        else:
            click.echo(f"Attempting to query {key} from the ToyChrod Network")
            res = requests.post(f"http://{THIS_IP}:{THIS_PORT}/query", \
                        json={"key_data":key})
        click.echo(res.json())

    else:
        click.echo(f"Must login first (using give_credentials command)")

@cli.command()
@click.option('--sim_attr',\
                type= click.Choice(["write", "read", "joined"]), \
                required = True \
                )
@click.option(  '--ntrials', \
                default=1, \
                type=int)
@click.option(  '-o', \
                '--output_dir', \
                default=None, \
                type=str)
def simulate(sim_attr, ntrials, output_dir):
    '''
    SImulates network's throughput
    simulation attribute must be one of [ write | read | joined ]
    '''
    if hasLoggedIn:
        res_arr = np.zeros(ntrials)
        for i in range(ntrials):
            click.echo(f"Attempting to get network's overlay for simulation")
            # get overlay
            res_overlay = (requests.get(f"http://{THIS_IP}:{THIS_PORT}/overlay")).json()
            net_overlay = res_overlay["Overlay"]["Overlay"]
            click.echo("Found network's overlay \n Constructing Simulator")
            # construct simulator
            sim = simulator.Simulator(net_overlay)
            # get input file from simulation_attribute
            if sim_attr == "write":
                sim.insert_requests(
                    filepath="data/insert.txt",\
                    mode="inserts"
                    )
            elif sim_attr == "read":
                sim.insert_requests(
                    filepath="data/query.txt",\
                    mode="queries"
                    )
            elif sim_attr == "joined":
                sim.insert_requests(
                    filepath="data/requests.txt",\
                    mode="requests"
                    )
            else:
                click.echo("ERROR")
            result = sim.simulate(output_dir)
            res_arr[i] = result[0]
        if ntrials == 1:
            click.echo(f"Average {sim_attr} throughput is {result[0]} (requests/sec) for {result[1]} requests.")
        else:
            click.echo(f"Average {sim_attr} throughput is {res_arr.mean()} +/- {res_arr.std()} (requests/sec) for {result[1]} requests, {ntrials} trials.")

if __name__=="__main__":

    global BOOTSTRAP_IP, THIS_IP, THIS_PORT, hasLoggedIn, hasJoined
    hasLoggedIn=False
    hasJoined=False

    print("\x1b[36m~~~~~~~~~~~~~~~~~~Distrib ToyChord (CLI)~~~~~~~~~~~~~~~~~~\x1b[0m\n.\
            Developed by Team Rocket . Prepare for trouble and make it double!\n \
                                    . \x1b[33mAnd as always.......Enjoy!\x1b[0m")



    register_repl(cli)
    cli()
# give_credentials()
