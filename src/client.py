"""CD Chat client program"""
import logging
import sys
import os
import fcntl
import socket
import selectors

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.name = name
        self.channel=None
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selectors = selectors.DefaultSelector()
        

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.sock.connect(("localhost",5555))
        self.selectors.register(self.sock,selectors.EVENT_READ,self.read)
        dataa=CDProto.register(self.name)
        CDProto.send_msg(self.sock, dataa)

    def read(self,conn,mask):
        dataa = CDProto.recv_msg(self.sock)
        logging.debug('received "%s', dataa)
        if dataa.command=="message":
            print(dataa.channel ," -> ", dataa.message)
        elif dataa.command=="join":
            print("Joined channel", dataa.channel)
        elif dataa.command=="register":
            print("Registered as", dataa.name)

    def got_keyboard_data(self,stdin,mask):
        input=stdin.read()
        if input.startswith("/join"):
            dataa=CDProto.join(input[6:-1])
            CDProto.send_msg(self.sock, dataa)
            self.channel=dataa.channel
        elif input.startswith("exit"):
            self.sock.close()
            sys.exit("Bye!" )

        else:
            dataa=CDProto.message(input[:-1],self.channel)
            CDProto.send_msg(self.sock, dataa)
        

    def loop(self):
        """Loop indefinetely."""
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
        self.selectors.register(sys.stdin, selectors.EVENT_READ, self.got_keyboard_data)
        while True:
            sys.stdout.write('Type something and hit enter: ')
            sys.stdout.flush()
            for k, mask in self.selectors.select():
                callback = k.data
                callback(k.fileobj,mask)