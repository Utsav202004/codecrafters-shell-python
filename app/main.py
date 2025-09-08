import sys # importing sys module for system specific functions


def main():

    while True: # creating a REPL

        sys.stdout.write("$ ") # diff from print, do not print \n (newline)
        command = input() # taking and storing the input

        parts = command.split()

        if not parts:
            continue # handling empty inputs


        if command == 'exit 0':
            break

        elif parts[0] == 'echo': # builtin echo
            print(" ".join(parts[1:]))

        else:
            print(f"{command}: command not found") 


if __name__ == "__main__":
    main()
