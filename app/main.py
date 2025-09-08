import sys # importing sys module for system specific functions
import os

types = {
    'exit'
}

commands = {
    'exit' : lambda exit_code : os._exit(int(exit_code)),
    'echo' : lambda *args : print(" ".join(args)),
    'type' : lambda type : print(f"{type} is a shell builtin") if (type in commands) else print(f"{type}: not found"),
}

def main():

    while True: # creating a REPL

        sys.stdout.write("$ ")  # diff from print, does not print \n (newline)

        command_with_arg = input().split() # taking and storing the command and arguments as list

        command = command_with_arg[0] # the command 

        if not command in commands:
            print(f"{command}: command not found")
            continue

        commands[command](*command_with_arg[1:]) # passing the argument to the required command function


if __name__ == "__main__":
    main()
