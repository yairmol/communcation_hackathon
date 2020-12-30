import socket
import config
from struct import pack, unpack, error
import getch
import queue
import time
import asyncio
import sys
import select
import tty
import termios
import random

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def isData():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def kbhit():
        dr, dw, de = select.select([sys.stdin], [], [], 0)
        return dr != []

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

    async def start(self):
        print(f"Client started, listening for offer requests...")
        while True:
            # wait for a game invite from a server
            msg, (ip, port) = self.udp_socket.recvfrom(7)
            if config.DEBUG or ip not in [config.MY_IP, '172.1.0.77']:
                continue
            try:
                cookie, flag, tcp_port = unpack('!IbH', msg)
            except error:
                continue
            # check validity
            if cookie != 0xfeedbeef or flag != 2:
                print(f"bad invite {(cookie, flag, tcp_port)} from {(ip, port)}, disregarding")
                continue
            print(f"Received offer from {ip}, attempting to connect...")
            await self.join_game(ip, tcp_port)
    
    async def join_game(self, ip, port):
        print(f"open connection to {(ip, port)}")
        reader, writer = await asyncio.open_connection(ip, port)
        writer.write(f"{self.name}\n".encode())
        await writer.drain()
        game_data = (await reader.read(1024)).decode()
        self.print_data(game_data)
        receiving_thread = self.data_receive()
        sending_thread = self.data_send(writer)
        rec_task = asyncio.create_task(receiving_thread)
        send_task = asyncio.create_task(sending_thread)
        await asyncio.sleep(10)
        rec_task.cancel()
        send_task.cancel()
        self.char_queue = queue.Queue()
        msg = (await reader.read(2048)).decode()
        print("\n",msg)
        writer.close()
        await writer.wait_closed()
        print("closed")

    def print_data(self, data):

        print(''.join(bcolors.HEADER + data))
        

    async def data_send(self, writer):
        try:
            while True:
                if not self.char_queue.empty():
                    writer.write(self.char_queue.get().encode('utf-8'))
                else:
                    await asyncio.sleep(0.00001)
        except asyncio.CancelledError:
            return

    async def data_receive(self):
        try:
            while True:
                if True: #isData():
                    if not kbhit():
                        continue
                    c = getch.getche()
                    # c = sys.stdin.read(1)
                    # print(c, end='')
                    # sys.stdout.flush()
                    self.char_queue.put(c)
                    await asyncio.sleep(0.00001)
        except asyncio.CancelledError:
            return


def main():
    client = Client("LMAO")
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        asyncio.run(client.start())
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    main()