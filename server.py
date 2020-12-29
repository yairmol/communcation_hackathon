import config
import socket
from struct import pack, unpack
import asyncio
from enum import Enum, auto
import random
import time

NAME = 0
ADDR = 1
READER = 2
WRITER = 3
COUNTER = 4
GROUP = 5

GAME_TIME = 10

class ServerState(Enum):
    SENDING_INVITES = auto()
    IN_GAME = auto()


class Server():
    def __init__(self):
        self.state = ServerState.SENDING_INVITES
        self.ip_address = config.MY_IP
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # enable broadcasts
        self.invite = pack('IbH', 0xfeedbeef, 2, 2077)
        self.clients = []
        self.group_1 = []
        self.group_2 = []
        self.server = None
        self.end_time = 0
        self.game_counter = 0

    async def make_game(self):
        async def make_client_listener(client, game_counter):
            while self.state == ServerState.IN_GAME and game_counter == self.game_counter:
                reader: asyncio.StreamReader = client[READER]
                chars = (await reader.read(1)).decode()
                print(f"got message from {client[NAME]}: {chars}")
                client[COUNTER] += len(chars)
            client[WRITER].close()
        # async def print_game_results(self):
        #     if self.state == ServerState.SENDING_INVITES:
        #         print(self.end_game_message())

        print("in game")
        msg = self.game_data_message()
        tasks = []
        for client in self.clients:
            client[WRITER].write(msg.encode())
            tasks.append(client[WRITER].drain())
            tasks.append(make_client_listener(client, self.game_counter))
        asyncio.gather(*tasks)
        
        #endgame
        
    def game_data_message(self):
        msg = "Welcome to Keyboard Spamming Battle Royale.\nGroup 1:\n==\n"
        for name in self.group_1:
            msg += name + "\n"
        msg += "\nGroup 2:\n==\n"
        for name in self.group_2:
            msg += name + "\n"
        msg += "\nStart pressing keys on your keyboard as fast as you can!!\n"
        return msg

    def end_game_message(self):
        sum_1 = 0
        sum_2 = 0
        for client in self.clients:
            if client[GROUP] == 1:
                sum_1 += client[COUNTER]
            else:
                sum_2 += client[COUNTER]
        msg = "Game over!\nGroup 1 typed in " + str(sum_1) + " characters. Group 2 typed in " + str(sum_2) + " characters.\n"
        if sum_1 > sum_2:
            msg += "Group 1 wins!\nCongratulations to the winners:\n==\n"
            for name in self.group_1:
                msg += name + "\n"
        elif sum_1 < sum_2:
            msg += "Group 2 wins!\nCongratulations to the winners:\n==\n"
            for name in self.group_2:
                msg += name + "\n"
        else:
            msg += "It's a Tie!"
        return msg

      
    async def send_invites(self):
        i = 0
        while True:
            if i == 10:
                self.state = ServerState.IN_GAME
                i = 0
                # self.end_time = time.time() + GAME_TIME
                asyncio.create_task(self.make_game())
                await asyncio.sleep(10)
                print(self.end_game_message())
                self.clients.clear()
                self.group_1.clear()
                self.group_2.clear()
                self.game_counter += 1
                self.state = ServerState.SENDING_INVITES
            if self.state == ServerState.SENDING_INVITES: 
                self.udp_socket.sendto(self.invite, (config.MY_IP if config.DEBUG else '172.1.255.255', config.INVITES_PORT))
                await asyncio.sleep(1)
                i += 1

        
    def add_connection(self):
        async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            if self.state == ServerState.SENDING_INVITES:
                addr = writer.get_extra_info('peername')
                print(f"Recivied connection request from {addr}")
                message = await reader.read(1024)
                client_name = message.decode()
                new_line_idx = client_name.find('\n')
                if new_line_idx != -1:
                    client_name = client_name[:new_line_idx]
                print(client_name)
                group = random.randint(1, 2)
                self.clients.append([client_name, addr, reader, writer, 0, group])
                if group == 1:
                    self.group_1.append(client_name)
                else:
                    self.group_2.append(client_name)

        return handle_connection 
        
    async def start(self):
        print(f"Server started, listening on IP address {config.MY_IP}")
        self.server = await asyncio.start_server(self.add_connection(), self.ip_address, 2077)
        asyncio.create_task(self.send_invites())
        async with self.server:
            await self.server.serve_forever()
        
        
def main():
    server = Server()
    asyncio.run(server.start())

if __name__ == "__main__":
    main()