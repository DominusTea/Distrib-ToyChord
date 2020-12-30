from cmd import Cmd
import requests
import os

class MyPrompt(Cmd):
    print("~~~~~~~~~~~~~~~~~~ToyChord (CLI)~~~~~~~~~~~~~~~~~~\n.\
            Developed by Team Rocket . Prepare for trouble and make it double!\
                                    Enjoy!")

    def do_exit(self, inp):
        '''Exiting the ToyChord Command Line Interface.'''
        print("Exiting the ToyChord Command Line Interface. Bye")
        return True

    def do_cli_Manual(self, inp):
        '''Manual for the application.'''
        print("\n\n----------\nCommands:\n----------\n")
        print("help                  Show a list of commands with 'help' or information for a command x with 'help x'")
        print("cli_Manual            Show a list of commands with specific information")
        print("energy_group67        Interact with cli-server with (login, logout, reset, healthcheck, admin, ...)")
        print("exit                  Exit the cli-application")
        print()

    def do_energy_group67(self, inp):
        '''Interact with cli-server.'''
        x = make_command_executable(inp)
        if x != '':
            #home_path = str(Path.home())
            #command = "python " + home_path + "/Desktop/TL19-67/cli-client/energy_group67.py " + x
            command = "python ../CLI/energy_group67.py " + x
            os.system(command)


if __name__ == '__main__':
    cli = MyPrompt()
    cli.cmdloop()
