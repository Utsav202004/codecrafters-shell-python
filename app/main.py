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
        elif executible_path := self.find_in_path(cmd):
            print(f"{cmd} is {executible_path}")
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

    def run(self):  # Main loop - the repl 

        while True:
            try:
                sys.stdout.write("$ ")

                user_input = input().strip()

                if not user_input:  # empty input
                    continue

                parts = self.command_parser(user_input)
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