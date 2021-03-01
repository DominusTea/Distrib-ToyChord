import click
from click_repl import register_repl

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
    print("--------------------------------------\n")

@cli.command()
def hello():
    click.echo("Hello world!")

print("\x1b[35m~~~~~~~~~~~~~~~~~~Distrib ToyChord (CLI)~~~~~~~~~~~~~~~~~~\x1b[0m\n.\
        Developed by Team Rocket . Prepare for trouble and make it double!\n \
                                . \x1b[34mAnd as always.......Enjoy!\x1b[0m")

register_repl(cli)
cli()
