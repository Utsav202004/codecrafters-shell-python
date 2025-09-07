import sys # importing sys module for system specific functions


def main():
    sys.stdout.write("$ ") # this is diff from normal print as it does not print the newline at end

    command = input() # this takes a command as an input 

    print(f"{command}: command not found")


if __name__ == "__main__":
    main()
