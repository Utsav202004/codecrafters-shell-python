'''
Build your own Shell project - Implementing in python

Worked on:
> builtins
> quoting
> I/O redirection

'''

import os
import sys
from typing import List, Tuple, Optional
import readline

class Shell:

    # Redirection mapping - 'operator' : (stdout/err, true/false)
    REDIRECT_OPS = {
        '>': (1, False),
        '1>': (1, False),
        '>>': (1, True),
        '1>>': (1, True),
        '2>': (2, False),
        '2>>': (2, True),
    }

    def __init__(self):
        
        self.builtins = {   # storing builtin functions
            'echo' : self.builtin_echo,
            'exit' : self.builtin_exit,
            'pwd' : self.builtin_pwd,
            'type' : self.builtin_type,
            'cd' : self.builtin_cd,
        }

        self.setup_autocomplete() # making a autocomplete function

    # --- Builtin Commands ---

    def builtin_echo(self, *args): # printing arg sep by spaces
        print(" ".join(args))

    def builtin_exit(self, *args): # exit shell - with given exit code
        exit_code = int(args[0]) if args else 0
        sys.exit(exit_code)

    def builtin_pwd(self, *args): # printing working directory
        print(os.getcwd())

    def builtin_type(self, *args): # showing type of command
        if not args:
            return
        
        cmd = args[0]
        if cmd in self.builtins:
            print(f"{cmd} is a shell builtin")
        elif executable_path := self.find_in_path(cmd):
            print(f"{cmd} is {executable_path}")
        else:
            print(f"{cmd}: not found")

    def builtin_cd(self, *args): # changing directory
        path = args[0] if args else "~"
        expanded_path = os.path.expanduser(path)

        try:
            os.chdir(expanded_path)
        except FileNotFoundError:
            print(f"cd: {path}: No such file or directory", file=sys.stderr)
        except PermissionError:
            print(f"cd: {path}: Permission denied", file=sys.stderr)


    # --- Command Execution ---

    def find_in_path(self, command: str) -> Optional[str]:    # searching for executable in path directories
        for directory in os.environ.get('PATH', '').split(":"):
            full_path = os.path.join(directory, command)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
        return None
    
    def execute_command(self, command: str, args:List[str], redirect_info: Optional[Tuple[str, int, bool]] = None):
        # Executing command with optional redirections
        
        if redirect_info:
            file_path, fd_num, append_mode = redirect_info
            self._execute_with_redirect(command, args, file_path, fd_num, append_mode)
        else:
            # normal exe without redir
            if command in self.builtins:
                self.builtins[command](*args)
            elif self.find_in_path(command):
                self._execute_external(command, args)
            else:
                print(f"{command}: command not found", file=sys.stderr)

    def _execute_external(self, command: str, args: List[str]):
        pid = os.fork()

        if pid == 0:
            try:
                os.execvp(command, [command] + args)
            except OSError:
                print(f"{command}: command not found", file=sys.stderr)
                os._exit(127)
        else:
            os.waitpid(pid, 0) 

    def _execute_with_redirect(self, command: str, args: List[str], file_path: str, fd_num: int, append: bool):
        # executing command with output redirection
        if command in self.builtins:
            self._redirect_builtin(command, args, file_path, fd_num, append)
        elif self.find_in_path(command):
            self._redirect_external(command, args, file_path, fd_num, append)
        else:
            print(f"{command}: command not found", file=sys.stderr)

    def _redirect_builtin(self, command: str, args: List[str], file_path: str, fd_num: int, append: bool):
        # Redirect Builtin command output
        original = sys.stdout if fd_num == 1 else sys.stderr # changing std reference

        try:
            with open(file_path, 'a' if append else 'w') as f:
                if fd_num == 1:
                    sys.stdout = f  # shifting pipe output
                else:
                    sys.stderr = f
                
                self.builtins[command](*args)
        finally:
            if fd_num == 1:
                sys.stdout = original # restoring default pipe str
            else:
                sys.stderr = original
    
    def _redirect_external(self, command: str, args: List[str], file_path: str, fd_num: int, append: bool) -> None:
        # Redirect external command output
        pid = os.fork()

        if pid == 0:    # child process
            try:
                flags = os.O_WRONLY | os.O_CREAT # flags needed in both the cases
                flags |= os.O_APPEND if append else os.O_TRUNC

                fd = os.open(file_path, flags, 0o644)
                os.dup2(fd, fd_num)
                os.close(fd)

                os.execvp(command, [command] + args) # executing external command
            except OSError:
                print(f"{command}: command not found", file=sys.stderr)
                os._exit(127)
        else:   # parent process
            os.waitpid(pid, 0)


    # --- parsing ---

    def parse_command_line(self, user_input: str) -> List[str]: # adressing quotes
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
    
    def find_redirection(self, parts: List[str]) -> Tuple[ Optional[str], List[str], Optional[Tuple[str, int, bool]]]:
        '''
        find and parse redirection operators in command parts
        tuple (command(optional as null), argumnets list, tuple of path(optional), file descriptor, and the append yes no)
        finding and parsing any redirection operator
        '''
        for op in self.REDIRECT_OPS:
            if op in parts:
                index = parts.index(op)

                # edge cases - working on syntax - missing command or target path
                if index == 0:
                    print("syntax error: missing command", file=sys.stderr)
                    return None, [], None
                
                if index + 1 >= len(parts):
                    print("syntax error: missing target path", file=sys.stderr)
                    return None, [], None
            
                # Extracting the info 
                command = parts[0]
                args = parts[1: index]
                file_path = parts[index + 1]
                fd_num, append = self.REDIRECT_OPS[op]

                return command, args, (file_path, fd_num, append)
        
        # No redirection case
        if parts:
            return parts[0], parts[1:], None
        return None, [], None # hanling all edge cases


    # -- Autocompletion -- 

    def setup_autocompletiion(self):

        readline.set_completer(self.comlete_command)    # setting completer function
        readline.parse_and_bind('tab: complete')    # binding
        readline.set_completer_delims(' \t\n;')     # delimiter

    def complete_command(self, text, state):

        line = readline.get_line_buffer()

        if not line.strip() or line.strip() == text:
        
            matches = [cmd for cmd in self.builtins.keys() if cmd.startswith(text)]

            if state < len(matches):
                return matches[state]
            
        return None
    

    # --- Main Loop ---
    
    def run(self):  # Main loop - the repl 

        while True:
            try:
                sys.stdout.write("$ ") # displaying prompt
                sys.stdout.flush()

                user_input = input().strip()
                if not user_input:  # empty input
                    continue

                parts = self.parse_command_line(user_input) # parsing command line
                if not parts:
                    continue

                # configuring redirection if any
                command, args, redirect_info = self.find_redirection(parts)
                if command is None:
                    continue
        
                self.execute_command(command, args, redirect_info)


            except EOFError: # ctrlD usage
                print()
                break
            except KeyboardInterrupt: # ctrlC usage
                print()
                continue

def main():
    shell = Shell()
    shell.run()

if __name__ == "__main__":
    main()