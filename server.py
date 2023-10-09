import socket
import random
import string
import time
from threading import Thread
import os
import shutil
import pathlib
from pathlib import Path

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None

    def start(self):
        # Create a socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the specified address and port
        self.server_socket.bind((self.host, self.port))
        # Listen for incoming connections
        self.server_socket.listen()
        # print(f"Server listening on {self.host}:{self.port}")
        print(f"Server listening on {self.host}:{self.port}")

        # while True:
        while True:
            # Accept incoming connections
            client_socket, client_address = self.server_socket.accept()
            # print(f"Accepted connection from {client_address}")
            print(f"Accepted connection from {client_address}")
            # send random eof token
            eof = self.generate_random_eof_token()
            client_socket.sendall(eof.encode())
            # Handle the client requests using ClientThread
            client_thread = ClientThread(self, client_socket, client_address, eof)
            client_thread.start()


    def get_working_directory_info(self, working_directory):
        """
        Creates a string representation of a working directory and its contents.
        :param working_directory: path to the directory
        :return: string of the directory and its contents.
        """
        dirs = "\n-- " + "\n-- ".join(
            [i.name for i in Path(working_directory).iterdir() if i.is_dir()]
        )
        files = "\n-- " + "\n-- ".join(
            [i.name for i in Path(working_directory).iterdir() if i.is_file()]
        )
        dir_info = f"Current Directory: {working_directory}:\n|{dirs}{files}"
        return dir_info


    def generate_random_eof_token(self):
        """Helper method to generates a random token that starts with '<' and ends with '>'.
        The total length of the token (including '<' and '>') should be 10.
        Examples: '<1f56xc5d>', '<KfOVnVMV>'
        return: the generated token.
        """

        characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
        eof = "<" + ''.join(random.choice(characters) for i in range(8)) + ">"
        return eof


    def receive_message_ending_with_token(self,active_socket, buffer_size, eof_token):
        """
        Same implementation as in receive_message_ending_with_token() in client.py
        A helper method to receives a bytearray message of arbitrary size sent on the socket.
        This method returns the message WITHOUT the eof_token at the end of the last packet.
        :param active_socket: a socket object that is connected to the server
        :param buffer_size: the buffer size of each recv() call
        :param eof_token: a token that denotes the end of the message.
        :return: a bytearray message with the eof_token stripped from the end.
        """

        file_content = bytearray()

        while True:
            packet = active_socket.recv(buffer_size)
            if packet[-10:] == eof_token.encode():
                file_content += packet[:-10]
                break
            file_content += packet

        return file_content


    def handle_cd(self, current_working_directory, new_working_directory):
        """
        Handles the client cd commands. Reads the client command and changes the current_working_directory variable
        accordingly. Returns the absolute path of the new current working directory.
        :param current_working_directory: string of current working directory
        :param new_working_directory: name of the sub directory or '..' for parent
        :return: absolute path of new current working directory
        """

        try:
            os.chdir(os.path.join(current_working_directory, new_working_directory))
        except os.error:
            print("Error in path! Server can't find this directory: ", new_working_directory)
        print("*****************************getced",os.getcwd())
        return os.getcwd()


    def handle_mkdir(self, current_working_directory, directory_name):
        """
        Handles the client mkdir commands. Creates a new sub directory with the given name in the current working directory.
        :param current_working_directory: string of current working directory
        :param directory_name: name of new sub directory
        """

        try:
            os.mkdir(os.path.join(current_working_directory, directory_name))
            print("Directory created!!!!!!!")
        except os.error:
            print("Server facing error in creating new directory!")
            return os.getcwd()


    def handle_rm(self, current_working_directory, object_name):
        """
        Handles the client rm commands. Removes the given file or sub directory. Uses the appropriate removal method
        based on the object type (directory/file).
        :param current_working_directory: string of current working directory
        :param object_name: name of sub directory or file to remove
        """

        file_path = os.path.join(current_working_directory, object_name)

        # check if file or directory exists
        if os.path.isfile(file_path) or os.path.islink(file_path):
            # remove file
            os.remove(file_path)

        elif os.path.isdir(file_path):
            # remove directory and all its content
            shutil.rmtree(file_path, ignore_errors=True)

        else:
            print("Server facing error while deleting file: ", object_name)
            return os.getcwd()


    def handle_ul(self, current_working_directory, file_name, service_socket, eof_token):
        """
        Handles the client ul commands. First, it reads the payload, i.e. file content from the client, then creates the
        file in the current working directory.
        Use the helper method: receive_message_ending_with_token() to receive the message from the client.
        :param current_working_directory: string of current working directory
        :param file_name: name of the file to be created.
        :param service_socket: active socket with the client to read the payload/contents from.
        :param eof_token: a token to indicate the end of the message.
        """

        print("*****************************getcwd ul",current_working_directory)
        file_path = os.path.join(current_working_directory, file_name)

        with open(file_path, 'wb') as file:
            file_content = self.receive_message_ending_with_token(service_socket, 1024, eof_token)
            file.write(file_content)

        print("File successfully uploaded!!!!")

    def handle_dl(self, current_working_directory, file_name, service_socket, eof_token):
        """
        Handles the client dl commands. First, it loads the given file as binary, then sends it to the client via the
        given socket.
        :param current_working_directory: string of current working directory
        :param file_name: name of the file to be sent to client
        :param service_socket: active service socket with the client
        :param eof_token: a token to indicate the end of the message.
        """

        print("*****************************getcwd dl", current_working_directory)
        file_path = os.path.join(current_working_directory, file_name)

        with open(file_path, 'rb') as file:
            file_content = file.read() + eof_token.encode()
            service_socket.sendall(file_content)

    def handle_info(self, current_working_directory, file_name, service_socket, eof_token):
        """
        Handles the client info commands. Reads the size of a given file.
        :param current_working_directory: string of current working directory
        :param file_name: name of sub directory or file to remove
        :param service_socket: active service socket with the client
        :param eof_token: a token to indicate the end of the message.
        """
        file_path = os.path.join(current_working_directory, file_name).replace(' ', '_')

        try:
            # Get the size of the file
            file_size = os.path.getsize(file_path)

            # Prepare the response message
            response = f"Size of {file_name}: {file_size} bytes"

            # Send the response to the client
            service_socket.sendall((response + eof_token).encode())
        except FileNotFoundError:
            # If the file is not found, send an error message to the client
            response = f"File '{file_name}' not found"
            service_socket.sendall((response + eof_token).encode())
        except Exception as e:
            # Handle other exceptions and send an error message to the client
            response = f"Error: {e}"
            service_socket.sendall((response + eof_token).encode())

        # Print the response on the server side (for debugging)
        print(response)

    def handle_mv(self, current_working_directory, file_name, destination_name):
        """
        Handles the client mv commands. First, it looks for the file in the current directory, then it moves or renames
        to the destination file depending on the nature of the request.
        :param current_working_directory: string of current working directory
        :param file_name: name of the file tp be moved / renamed
        :param destination_name: destination directory or new filename
        """
        source_path = os.path.join(current_working_directory, file_name)

        # Check if the source file exists
        if os.path.exists(source_path):
            # Check if the destination is a directory or a new filename
            if os.path.isdir(destination_name):
                # Destination is a directory, move the file to the destination directory
                destination_path = os.path.join(destination_name, file_name)
                os.rename(source_path, destination_path)
                print(f"Moved '{file_name}' to '{destination_path}'")
            else:
                # Destination is a new filename, rename the file
                destination_path = os.path.join(current_working_directory, destination_name)
                os.rename(source_path, destination_path)
                print(f"Renamed '{file_name}' to '{destination_name}'")
        else:
            print(f"File '{file_name}' does not exist in the current directory.")


class ClientThread(Thread):

    def __init__(self, server: Server, service_socket: socket.socket, address: str, eof_token: str):
        Thread.__init__(self)
        self.server_obj = server
        self.service_socket = service_socket
        self.address = address
        self.eof_token = eof_token

    def run(self):

        # print ("Connection from : ", self.address)
        print(f"Connection from : ", {self.address})

        # establish working directory
        current_working_dir = pathlib.Path(__file__).parent.resolve()

        # send the current dir info
        self.service_socket.sendall((self.server_obj.get_working_directory_info(current_working_dir) + self.eof_token).encode())

        # while True:
        while True:
            command = self.server_obj.receive_message_ending_with_token(self.service_socket, 1024, self.eof_token)
            command = command.decode()

            # get the command and arguments and call the corresponding method
            if command.lower() == "exit":
                break


            if command.startswith("mkdir "):
                self.server_obj.handle_mkdir(current_working_dir, command[6:])
            elif command.startswith("cd "):
                current_working_dir = self.server_obj.handle_cd(current_working_dir, command[3:])
            elif command.startswith("rm "):
                self.server_obj.handle_rm(current_working_dir, command[3:])
            elif command.startswith("ul "):
                self.server_obj.handle_ul(current_working_dir, command[3:], self.service_socket, self.eof_token)
            elif command.startswith("dl "):
                self.server_obj.handle_dl(current_working_dir, command[3:], self.service_socket, self.eof_token)
            elif command.startswith("info "):
                self.server_obj.handle_info(current_working_dir, command[5:], self.service_socket, self.eof_token)
            elif command.startswith("mv "):
                args = command.split(" ")
                if len(args) == 3:
                    _, source, destination = args
                    self.server_obj.handle_mv(current_working_dir, source, destination)
            else:
                print("Invalid command. Supported commands: cd, mkdir, rm, ul, dl, info, mv, exit")

            time.sleep(1)
            # send current dir info
            self.service_socket.sendall((self.server_obj.get_working_directory_info(current_working_dir) + self.eof_token).encode())
            #self.service_socket.sendall((self.server_obj.get_working_directory_info(current_working_dir) + self.eof_token).encode())

        # print('Connection closed from:', self.address)
        print(f'Connection closed from:', {self.address})
        self.service_socket.close()


def run_server():
    HOST = "127.0.0.1"
    PORT = 65432

    server = Server(HOST, PORT)
    server.start()


if __name__ == '__main__':
    run_server()