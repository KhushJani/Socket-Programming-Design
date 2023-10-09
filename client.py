import socket
import os
import pathlib

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.eof_token = None


    def receive_message_ending_with_token(self, active_socket, buffer_size, eof_token):
        """
        Same implementation as in receive_message_ending_with_token() in server.py
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
            if packet[-len(eof_token):] == eof_token.encode():
                file_content += packet[:-len(eof_token)]
                break
            file_content += packet

        return file_content


    def initialize(self, host, port):
        """
        1) Creates a socket object and connects to the server.
        2) receives the random token (10 bytes) used to indicate end of messages.
        3) Displays the current working directory returned from the server (output of get_working_directory_info() at the server).
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param host: the ip address of the server
        :param port: the port number of the server
        :return: the created socket object
        """

        # print('Connected to server at IP:', host, 'and Port:', port)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        print("Connected to server at IP:", host, "and Port:", port)

        # print('Handshake Done. EOF is:', eof_token)
        eof_token = client_socket.recv(1024)
        eof_token = eof_token.decode()
        print("Handshake Done. EOF is:", eof_token)

        print(self.receive_message_ending_with_token(client_socket, 1024, eof_token).decode())
        return client_socket, eof_token


    def issue_cd(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full cd command entered by the user to the server. The server changes its cwd accordingly and sends back
        the new cwd info.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        """

        command = command_and_arg + eof_token
        client_socket.sendall(command.encode())
        print(self.receive_message_ending_with_token(client_socket, 1024, eof_token).decode())


    def issue_mkdir(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full mkdir command entered by the user to the server. The server creates the sub directory and sends back
        the new cwd info.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        """

        command = command_and_arg + eof_token
        client_socket.sendall(str.encode(command))

        response = self.receive_message_ending_with_token(client_socket, 1024, eof_token)
        print("Received response from server:", response.decode())

    def issue_rm(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full rm command entered by the user to the server. The server removes the file or directory and sends back
        the new cwd info.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        """

        command = command_and_arg + eof_token
        client_socket.sendall(str.encode(command))
        print(self.receive_message_ending_with_token(client_socket, 1024, eof_token).decode())


    def issue_ul(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full ul command entered by the user to the server. Then, it reads the file to be uploaded as binary
        and sends it to the server. The server creates the file on its end and sends back the new cwd info.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        """

        file_name = command_and_arg.split("ul ")[1]
        file_path = os.path.join(pathlib.Path(__file__).parent.resolve(), file_name)

        if os.path.exists(file_path):
            client_socket.sendall(str.encode(command_and_arg + eof_token))

            with open(file_path, 'rb') as f:
                file = f.read() + eof_token.encode()
                client_socket.sendall(file)
            print(self.receive_message_ending_with_token(client_socket, 1024, eof_token).decode())

        else:
            print("File does not exist on the client!")




    def issue_dl(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full dl command entered by the user to the server. Then, it receives the content of the file via the
        socket and re-creates the file in the local directory of the client. Finally, it receives the latest cwd info from
        the server.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        :return:
        """

        file_name = command_and_arg.split("dl ")[1]
        file_path = os.path.join(pathlib.Path(__file__).parent.resolve(), file_name)
        # file_path -> assignment_folder\client\file_name

        client_folder_path = os.path.join(pathlib.Path(__file__).parent.resolve())
        # client folder path -> assignment_folder\client
        print("Client path ->", client_folder_path)
        # change given directory one level above
        #assignment_folder = os.path.split(client_folder_path)[0]
        # assignment_folder -> assignment_folder
        #print("Assignment folder ->", assignment_folder)
        server_path = (os.path.join(client_folder_path, 'server'))
        # server_path -> assignment_folder\server
        print("Server path ->", server_path)

        print("File Path ->",os.path.join(server_path, file_name))
        # Check in the server folder if the file exists or not and if it exists then only add in the client folder
        if os.path.exists(os.path.join(server_path, file_name)):
            client_socket.sendall(str.encode(command_and_arg + eof_token))

            file = self.receive_message_ending_with_token(client_socket, 1024, eof_token)
            with open(file_path, 'wb') as f:
                f.write(file)

            print(f"File '{file_name}' downloaded to '{file_path}'")
            print(self.receive_message_ending_with_token(client_socket, 1024, eof_token).decode())

        else:
            print("File does not exist in server!")



    def issue_info(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full info command entered by the user to the server. The server reads the file and sends back the size of
        the file.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        :return: the size of file in string
        """
        command = command_and_arg + eof_token
        client_socket.sendall(command.encode())
        print(self.receive_message_ending_with_token(client_socket, 1024, eof_token).decode())


    def issue_mv(self, command_and_arg, client_socket, eof_token):
        """
        Sends the full mv command entered by the user to the server. The server moves the file to the specified directory and sends back
        the updated. This command can also act as renaming the file in the same directory.
        Use the helper method: receive_message_ending_with_token() to receive the message from the server.
        :param command_and_arg: full command (with argument) provided by the user.
        :param client_socket: the active client socket object.
        :param eof_token: a token to indicate the end of the message.
        """
        command = command_and_arg + eof_token
        client_socket.sendall(command.encode())
        print(self.receive_message_ending_with_token(client_socket, 1024, eof_token).decode())


    def start(self):
        """
        1) Initialization
        2) Accepts user input and issue commands until exit.
        """
        # initialize
        client_socket, eof_token = self.initialize(self.host, self.port)


        # while True:
        while True:
            # get user input
            user_input = input(f"Enter the command -> ")

            # call the corresponding command function or exit
            if user_input.lower() == 'exit':
                break

            if user_input.startswith("cd "):
                self.issue_cd(user_input, client_socket, eof_token)
            elif user_input.startswith("mkdir "):
                self.issue_mkdir(user_input, client_socket, eof_token)
            elif user_input.startswith("rm "):
                self.issue_rm(user_input, client_socket, eof_token)
            elif user_input.startswith("ul "):
                self.issue_ul(user_input, client_socket, eof_token)
            elif user_input.startswith("dl "):
                self.issue_dl(user_input, client_socket, eof_token)
            elif user_input.startswith("info "):
                self.issue_info(user_input, client_socket, eof_token)
            elif user_input.startswith("mv "):
                self.issue_mv(user_input, client_socket, eof_token)
            else:
                print("Invalid command. Supported commands: cd, mkdir, rm, ul, dl, info, mv, exit")

        # print('Exiting the application.')
        print("Exiting the application.")


def run_client():
    HOST = "127.0.0.1"  # The server's hostname or IP address
    PORT = 65432  # The port used by the server

    client = Client(HOST, PORT)
    client.start()

if __name__ == '__main__':
    run_client()