import socket
import config
from struct import pack, unpack, error
import getch
import queue
import time
import asyncio

GAME_TIME = 10

class GameOverTimeOut(Exception):
    pass

class Client:
    def __init__(self, name):
        self.name = name
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(('', config.INVITES_PORT))
        self.char_queue = queue.Queue()
        self.timer_end = 0

    async def start(self):
        print(f"Client started, listening for offer requests...")
        while True:
            # wait for a game invite from a server
            msg, (ip, port) = self.udp_socket.recvfrom(8)
            if config.DEBUG or ip != config.MY_IP:
                continue
            try:
                cookie, flag, tcp_port = unpack('IbH', msg)
            except error:
                if len(msg) != 7:
                    continue
                cookie, flag, tcp_port = unpack('I', msg[:4]), unpack('b', msg[4:5]), unpack('H', msg[5:])
            # check validity
            if cookie != 0xfeedbeef or flag != 2:
                print(f"bad invite {(cookie, flag, tcp_port)} from {(ip, port)}, disregarding")
                continue
            print(f"Received offer from {ip}, attempting to connect...")
            await self.join_game(ip, tcp_port)
    
    async def join_game(self, ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        s.send(f"{self.name}\n".encode())
        game_data = s.recv(1024).decode()
        self.timer_end = time.time() + GAME_TIME
        self.print_data(game_data)
        receiving_thread = self.data_receive(s)
        sending_thread = self.data_send(s)
        asyncio.wait([receiving_thread, sending_thread], timeout=10)
        s.close()

    def print_data(self, data):
        print(''.join(data))

    async def data_send(self, s):
        while time.time() < self.timer_end:
            if not self.char_queue.empty():
                s.send(self.char_queue.get().encode('utf-8'))

    async def data_receive(self, s):
        while time.time() < self.timer_end:
            c = getch.getch()
            self.char_queue.put(c)

def main():
    client = Client("LMAO")
    asyncio.run(client.start())

if __name__ == "__main__":
    main()