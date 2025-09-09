import sys      # importing sys module for system specific functions
import os

def searcher(type):     # searching for a executbale file in the PATH
    path_string = os.environ.get('PATH', '')    # getting the path string
    dir_list = path_string.split(':')   # list of directories

    for dir in dir_list:    # searching
        full_path = os.path.join(dir, type)
        if os.path.exists(full_path) and os.access(full_path, os.X_OK):     # checking for the existence and access
                return full_path

    return None     # if nothing found 

def path_verifier(path):    # verying the path passed with cd
    f_path = "" # full path

    if (path[0] == '/' or path[0] != '.') and os.path.isdir(path):  # abs path
        return path
    
    elif path[0:2] == './' and os.path.isdir(f_path := os.path.join(os.getcwd(), path)):    # sub-dir
        return f_path
    
    elif path[0:3] == '../':    # parent dir
        count = 0
        for i in range(0, len(path), 3): # counting how much we need to move up in the directories
            if path[i] == '.':
                count += 1
            else:
                break
        
        cnt = count
        f_path = os.getcwd()
        ind = len(f_path) # figuring out the new path
        while(count > 0): # moving up the directories
            for ind in range(ind, 0, -1):
                if f_path[ind] == '/':
                    count -= 1
        if f_path := os.path.isdir(os.path.join(f_path[0:ind+1]), path[3*cnt:]):
            return f_path
        else:
            return None # invalid path
        
    else:   # invalid path
        return None
            
        
commands = {
    'exit' : lambda exit_code : os._exit(int(exit_code)),
    'echo' : lambda *args : print(" ".join(args)),
    'type' : lambda type : print(f"{type} is a shell builtin") if (type in commands) else ( print(f"{type} is {path}") if (path := searcher(type)) else print(f"{type}: not found")),
    'pwd' : lambda : print(os.getcwd()),
    'cd' : lambda path = '~' : os.chdir(expanded) if os.path.isdir(expanded := os.path.expanduser(path)) else print(f"cd: {path}: No such file or directory"),
}

def main():

    while True:     # creating a REPL

        sys.stdout.write("$ ")     # diff from print, does not print \n (newline)

        command_with_arg = input().split()      # taking and storing the command and arguments as list

        command = command_with_arg[0]   # the command 

        if command in commands:     # execute builtins
            commands[command](*command_with_arg[1:])    # passing the argument to the required command function

        else:   # executing commands in path
            full_path = searcher(command)
            if full_path:
                pid = os.fork()     # creating a child process

                if pid == 0:    # entering child process
                    try:
                        os.execvp(command, command_with_arg)
                    except OSError:     # if the command cannot be executed
                        print(f"{command}: command not found", file=sys.stderr)
                        os._exit(127)   # exiting with an error

                else:   # entering parent process
                    os.waitpid(pid, 0)  # parent needs to wait for the child process to end

            else:
                print(f"{command}: command not found")    
                  


if __name__ == "__main__":
    main()
