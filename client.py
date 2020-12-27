import socket
import scapy.all as scapy
import config
from struct import pack, unpack

class Client:
    def __init__(self, name):
        self.name = name
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('', config.INVITES_PORT))
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def start(self):
        print(f"Client started, listening for offer requests...")
        while True:
            # wait for a game invite from a server
            msg, (ip, port) = self.udp_socket.recvfrom(8)
            print(ip, port, len(msg))
            ip = '172.1.0.117'
            # parse message into 3 parts - cookie, flag and tcp port
            cookie, flag, tcp_port = unpack('IbH', msg)
            # check validity
            if cookie != 0xfeedbeef or flag != 2:
                print(f"bad invite {(cookie, flag, tcp_port)} from {(ip, port)}, disregarding")
            print(f"Received offer from {ip}, attempting to connect...")
            self.join_game(ip, tcp_port)
    
    def join_game(self, ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        s.send(f"{self.name}\n".encode())


def main():
    Client("LMAO").start()

if __name__ == "__main__":
    main()