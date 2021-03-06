import click
from click_repl import register_repl
import json
# for requesting
import requests

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
def join():
    if hasLoggedIn:
        click.echo(f"Attempting to join ToyChord P2P Network with ip = {THIS_IP}, port={THIS_PORT}, on bootstrap = {BOOTSTRAP_IP}")
        res = requests.get(f"http://{THIS_IP}:{THIS_PORT}/join")

    else:
        click.echo(f"Must login first (using give_credentials command)")
    # pass
@cli.command()
def depart():
    if hasLoggedIn:
        click.echo(f"Attempting to depart from ToyChrod P2P Network")
        res = requests.get(f"http://{THIS_IP}:{THIS_PORT}/depart")    
    else:
        click.echo(f"Must login first (using give_credentials command)")
@cli.command()
def print_all():
        if hasLoggedIn:
            click.echo(f"Local node running on ip{THIS_IP}:{THIS_PORT} has DHT:")
            res = requests.get(f"http://{THIS_IP}:{THIS_PORT}/print_all")
            click.echo(res.json())

if __name__=="__main__":

    global BOOTSTRAP_IP, THIS_IP, THIS_PORT, hasLoggedIn
    hasLoggedIn=False

    print("\x1b[36m~~~~~~~~~~~~~~~~~~Distrib ToyChord (CLI)~~~~~~~~~~~~~~~~~~\x1b[0m\n.\
            Developed by Team Rocket . Prepare for trouble and make it double!\n \
                                    . \x1b[33mAnd as always.......Enjoy!\x1b[0m")



    register_repl(cli)
    cli()
    # give_credentials()