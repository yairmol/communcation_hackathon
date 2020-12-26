import socket
import scapy.all as scapy
import config


def main():
    print(f"start listenting on {scapy.get_if_addr(config.CURRENT_NET)}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((scapy.get_if_addr(config.CURRENT_NET), config.INVITES_PORT))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # enable broadcasts
    print(str(sock.recv(1024)))

if __name__ == "__main__":
    main()