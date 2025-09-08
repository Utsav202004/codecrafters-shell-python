import sys # importing sys module for system specific functions


def main():

    while True: # creating a REPL

        sys.stdout.write("$ ") # diff from print, do not print \n (newline)
        command = input() # taking and storing the input

        if command.split()[0] == 'exit':
            return 0
        print(f"{command}: command not found") 


if __name__ == "__main__":
    main()
