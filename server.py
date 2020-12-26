import scapy.all as scapy
import sys
import config
import socket
import time


class Server():
    def __init__(self):
        self.ip_address = scapy.get_if_addr(config.CURRENT_NET)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # enable broadcasts

    def start(self):
        print(f"Server started, listening on IP address {scapy.get_if_addr(config.CURRENT_NET)}")
        for i in range(10):
            self.udp_socket.sendto(config.INVITE_MESSAGE, (scapy.get_if_addr(config.CURRENT_NET), config.INVITES_PORT))
            time.sleep(1)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "eth2":
            config.CURRENT_NET = config.TEST_NET
    Server().start()

if __name__ == "__main__":
    main()