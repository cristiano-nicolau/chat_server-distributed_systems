"""CD Chat server program."""
import logging
import socket
import selectors

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename="server.log", level=logging.DEBUG)


class Server:
    """Chat Server process."""
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM )
        self.sock.bind(("localhost",5555))
        self.sock.listen(9)
        self.selectors = selectors.DefaultSelector()
        self.selectors.register(self.sock,selectors.EVENT_READ, self.accept)
        self.dic={}

    def accept(self,sock, mask):
        conn,addr=self.sock.accept()    
        print('accepted', conn, 'from', addr)
        self.selectors.register(conn,selectors.EVENT_READ,self.read)
        self.dic[conn]=[None]
        
    def read(self,conn,mask):                                
            data = CDProto.recv_msg(conn)
            if not data is None:

                logging.debug('received "%s', data)

                if data.command == "register":
                    CDProto.send_msg(conn, data)
                elif data.command== "join":
                    if self.dic[conn]==None:
                        self.dic[conn].remove(None)
                    if data.channel not in self.dic[conn]:
                        self.dic[conn].append(data.channel)
                    CDProto.send_msg(conn, data)
                elif data.command== "message":
                    for key,value in self.dic.items():
                        if data.channel in value:
                            CDProto.send_msg(key, data)
            else:
                self.selectors.unregister(conn)
                conn.close()
                self.dic.pop(conn)
            

    def loop(self):
        """Loop indefinetely."""
        while True:
            events = self.selectors.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj , mask)