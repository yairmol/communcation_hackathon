import socket
import config
from struct import pack, unpack, error
import queue
import time
import asyncio
import sys
import select
import tty
import termios
import random
import aioconsole

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
        self.stdin = None
        self.stdout = None

    async def start(self):
        print(f"Client started, listening for offer requests...")
        self.stdin, self.stdout = await aioconsole.get_standard_streams()
        while True:
            # wait for a game invite from a server
            msg, (ip, port) = self.udp_socket.recvfrom(7)
            if config.DEBUG and ip not in config.EXCLUSIVE_IPS:
                continue
            try:
                cookie, flag, tcp_port = unpack(config.PACKING_FORMAT, msg)
            except error:
                continue
            # check validity
            if cookie != config.MAGIC_COOKIE or flag != config.FLAG:
                print(f"bad invite {(cookie, flag, tcp_port)} from {(ip, port)}, disregarding")
                continue
            print(f"Received offer from {ip}, attempting to connect...")
            try:
                await self.join_game(ip, tcp_port)
            except Exception:
                print("a connection error occured while playing but don't worry https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstleyVEVO")
    
    async def join_game(self, ip, port):
        self.char_queue = queue.Queue()
        try:
            # connect and receive game start message
            reader, writer = await asyncio.open_connection(ip, port)
            writer.write(f"{self.name}\n".encode())
            await writer.drain()
            game_data = (await reader.read(config.READ_BUFFER)).decode()
            self.print_data(game_data)
        except Exception:
            print(f"could not connect to {(ip, port)} :(")
        queue_event = asyncio.Event()
        # run a coroutine for reading typings from stdin
        rec_task = asyncio.create_task(self.data_receive(queue_event))
        # run a coroutine for sending typings to server
        send_task = asyncio.create_task(self.data_send(writer, queue_event))
        await asyncio.sleep(config.GAME_TIME)
        # close coroutines
        rec_task.cancel()
        send_task.cancel()
        # receive end game message
        end_game_msg = (await reader.read(config.READ_BUFFER)).decode()
        print("\n", end_game_msg, sep='')
        # close connection
        writer.close()
        await writer.wait_closed()

    def print_data(self, data):
        print(''.join(bcolors.HEADER + data))

    async def data_send(self, writer, queue_event):
        try:
            while True:
                await queue_event.wait()
                c = self.char_queue.get()
                writer.write(c.encode('utf-8'))
                if self.char_queue.empty():
                    queue_event.clear()
        except Exception:
            return

    async def data_receive(self, queue_event):
        try:
            while True:
                c = (await self.stdin.read(1)).decode()
                print(c, end='')
                sys.stdout.flush()
                self.char_queue.put(c)
                queue_event.set()
        except Exception:
            return


def main():
    client = Client(config.OUR_NAME)
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        asyncio.run(client.start())
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    main()