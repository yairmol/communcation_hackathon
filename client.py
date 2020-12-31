import socket
import config
from struct import pack, unpack, error
import queue
import asyncio
import sys
import select
import tty
import termios
import aioconsole
from config import Colors

RECIVE = 7

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
        self.queue_event = None

    async def start(self):
        print(f"Client started, listening for offer requests...")
        self.stdin, self.stdout = await aioconsole.get_standard_streams()
        while True:
            # wait for a game invite from a server
            msg, (ip, port) = self.udp_socket.recvfrom(RECIVE)
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
            try:
                await self.join_game(ip, tcp_port)
            except Exception:
                print(f"{Colors.WARNING}\nA connection error occured while playing but don't worry https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstleyVEVO {Colors.ENDC}")
                continue
    
    async def join_game(self, ip, port):
        try:
            # connect and receive game start message
            reader, writer = await asyncio.open_connection(ip, port)
            print(f"Received offer from {ip}, attempting to connect...")
        except Exception:
            # print(f"could not connect to {(ip, port)} :(")
            return
        writer.write(f"{self.name}\n".encode())
        await writer.drain()
        game_data = (await reader.read(config.READ_BUFFER)).decode()
        self.print_data(game_data)
        self.char_queue = queue.Queue()
        self.queue_event = asyncio.Event()
        # run a coroutine for reading typings from stdin
        rec_task = asyncio.create_task(self.data_receive())
        # run a coroutine for sending typings to server
        send_task = asyncio.create_task(self.data_send(writer))
        await asyncio.sleep(config.GAME_TIME)
        # close coroutines
        rec_task.cancel()
        send_task.cancel()
        # wait for tasks to be cancelled
        try:
            await rec_task
        except asyncio.CancelledError:
            pass
        try:
            await send_task
        except asyncio.CancelledError:
            pass
        # receive end game message
        end_game_msg = (await reader.read(config.READ_BUFFER)).decode()
        print("\n", end_game_msg, sep='')
        # close connection
        writer.close()
        await writer.wait_closed()

    def print_data(self, data):
        print(''.join(Colors.HEADER + data + Colors.ENDC))

    async def data_send(self, writer):
        try:
            while True:
                await self.queue_event.wait()
                c = self.char_queue.get()
                writer.write(c.encode('utf-8'))
                await writer.drain()
                if self.char_queue.empty():
                    self.queue_event.clear()
        except Exception:
            return

    async def data_receive(self):
        try:
            while True:
                c = (await self.stdin.read(1)).decode()
                print(c, end='')
                sys.stdout.flush()
                self.char_queue.put(c)
                self.queue_event.set()
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