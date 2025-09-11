import os
import sys

class Shell:

    def __init__(self):
        
        self.builtins = {   # storing builtin functions as instance var
            'echo' : self.builtin_echo,
            'exit' : self.builtin_exit,
            'pwd' : self.builtin_pwd,
            'type' : self.builtin_type,
            'cd' : self.builtin_cd,
        }

    def builtin_echo(self, *args):
        if not args:
            return
        print(" ".join(args))

    def builtin_exit(self, *args):
        exit_code = int(args[0]) if args else 0
        sys.exit(exit_code)

    def builtin_pwd(self, *args):
        print(os.getcwd())

    def builtin_type(self, *args):
        if not args:
            return
        
        cmd = args[0]
        if cmd in self.builtins:
            print(f"{cmd} is a shell builtin")
        elif executable_path := self.find_in_path(cmd):
            print(f"{cmd} is {executable_path}")
        else:
            print(f"{cmd}: not found")

    def builtin_cd(self, *args):
        path = args[0] if args else "~"
        expanded_path = os.path.expanduser(path)

        try:
            os.chdir(expanded_path)
        except FileNotFoundError:
            print(f"cd: {path}: No such file or directory", file=sys.stderr)
        except PermissionError:
            print(f"cd: {path}: Permission denied", file=sys.stderr)

    def find_in_path(self, command):
        path_dirs = os.environ.get('PATH', '').split(":")

        for directory in path_dirs:
            full_path = os.path.join(directory, command)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
        return None
    
    def execute_external(self, command, args):
        pid = os.fork()

        if pid == 0:
            try:
                os.execvp(command, [command] + args)
            except OSError:
                print(f"{command}: command not found", file=sys.stderr)
                os._exit(127)
        else:
            os.waitpid(pid, 0)


    def execute_command(self, command, args):
        if command in self.builtins:
                    method = self.builtins[command]
                    method(*args)
        elif self.find_in_path(command):
            self.execute_external(command, args)
        else:
            print(f"{command}: command not found")

    def command_parser(self, user_input): # adressing quotes
        curr_word = []
        words = []
        in_squotes = False
        in_dquotes = False
        i = 0

        while i < len(user_input): # parsing each char, keeping record
            char = user_input[i]

            # handling the escape backslash 
            if char == "\\" and i + 1 < len(user_input): # if backslash is last char
                next_char = user_input[i+1]

                if in_squotes: # in single quote, \ is literal \
                    curr_word.append(char)

                elif in_dquotes:
                    if next_char in ['"', '\\', '$', '`']: # handling edge cases
                        curr_word.append(next_char)
                        i += 1
                    else:
                        curr_word.append(char)

                else: # non single quotes case
                    curr_word.append(next_char)
                    i += 1
            
            # handling quote
            elif char == "'" and not (in_squotes or in_dquotes): # for single quote in double quote
                in_squotes = True
            elif char == "'" and in_squotes:
                in_squotes = False
            elif char == "\"" and not (in_dquotes or in_squotes): # for double q in single quote
                in_dquotes = True
            elif char == "\"" and in_dquotes:
                in_dquotes = False

            # handling spaces
            elif char == " " and not (in_squotes or in_dquotes):
                if curr_word:
                    words.append(''.join(curr_word))
                    curr_word = []
            else:
                curr_word.append(char)

            i += 1

        if curr_word:   # last curr word not added yet
            words.append(''.join(curr_word))

        return words
    
    def execute_and_redirect(self, command, args, file_path): # for > and 1>

        if command in self.builtins: # stdout works for parent process, non-builtin -> child process
            org_output = sys.stdout # ref to the original std output

            try:
                with open(file_path, 'w') as f:
                    sys.stdout = f  # changing the pipe to desired location

                    self.execute_command(command, args)

            finally:
                sys.stdout = org_output # restoring the pipe

        else:
            if self.find_in_path(command): # create a sep function for path executibles
                self.execute_external_and_redirect(command, args, file_path)
            else: # edge case
                print(f"{command}: command not found")

    def execute_external_and_redirect(self, command, args, file_path): # for > and 1> for a executible path

        pid = os.fork()

        if pid == 0: # child process
            try:
                fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC , 0o644) # write only, create if not exist, truncate if exists, permisions 0o644
                os.dup2(fd, 1)
                os.close(fd)

                os.execvp(command, [command] + args)

            except OSError:
                print(f"{command}: command not found", file= sys.stderr)
                os._exit(127)

        else:
            os.waitpid(pid, 0)

    def execute_redirect_err(self, command, args, file_path):

        if command in self.builtins:
            org_output = sys.stderr # storing reference to the stderr path 

            try:
                with open(file_path, 'w') as f:
                    f = sys.stderr

                self.execute_command(command, args)

            finally:
                sys.stderr = org_output

        else:
            if self.find_in_path(command):
                self.execute_external_redirect_err(command, args, file_path)
            else:
                print(f"{command}: command not found", file = sys.stderr)

    def execute_external_redirect_err(command, args, file_path):

        pid = os.fork()

        if pid == 0:
            try:
                fd = os.open(file_path, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0o644)
                os.dup2(fd, 2)
                os.close(fd)

                os.execvp(command, [command] + args)
            except OSError:
                print(f"{command}: command not found", file = sys.stderr)
                os._exit(127)

        else:
            os.waitpid(pid, 0)
        

    def run(self):  # Main loop - the repl 

        while True:
            try:
                sys.stdout.write("$ ")

                user_input = input().strip()

                if not user_input:  # empty input
                    continue

                parts = self.command_parser(user_input)

                if ">" in parts or "1>" in parts or "2>" in parts: # for redirection 
                    case_out = False
                    case_err = False

                    if ">" in parts:
                        ind = parts.index(">")
                        case_out = True
                    elif "1>" in parts:
                        ind = parts.index("1>")
                        case_out = True
                    else:
                        ind = parts.index("2>")
                        case_err = True

                    command_part = parts[: ind]
                    path_part = parts[ind + 1] if ind + 1 < len(parts) else None # edge case

                    if not command_part: # edge case - missing command part
                        print("syntax error: missing command part", file = sys.stderr)
                        continue

                    if not path_part: # edge case - missing path part
                        print("syntax error: missing path", file = sys.stderr)
                        continue
                    
                    if case_out:
                        self.execute_and_redirect(command_part[0], command_part[1:], path_part)
                    else:
                        self.execute_redirect_err(command_part[0], command_part[1:], path_part)

                elif "2>" in parts:
                    ind = parts.index("2>")

                else: # without redirection

                    command = parts[0]
                    args = parts[1:]
                    self.execute_command(command, args)
        
            except EOFError: # ctrlD usage
                print()
                break
            except KeyboardInterrupt: # ctrlC usage
                print()
                continue

if __name__ == "__main__":
    shell = Shell()
    shell.run()