import config
import socket
from struct import pack, unpack
import asyncio
from enum import Enum, auto
import random
from config import Colors

NAME = 0
ADDR = 1
READER = 2
WRITER = 3
COUNTER = 4
GROUP = 5

class ServerState(Enum):
    SENDING_INVITES = auto()
    IN_GAME = auto()


class Server():
    def __init__(self):
        self.state = ServerState.SENDING_INVITES
        self.ip_address = config.MY_IP
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # enable broadcasts
        self.invite = pack(config.PACKING_FORMAT, config.MAGIC_COOKIE, config.FLAG, config.SERVER_TCP_PORT)
        self.clients = []
        self.group_1 = []
        self.group_2 = []
        self.server = None
        self.game_counter = 0
        self.end_msg = None

    async def make_game(self):
        async def make_client_listener(client, game_counter, first_msg):
            try:
                client[WRITER].write(first_msg.encode())
                await client[WRITER].drain()
                while self.state == ServerState.IN_GAME and game_counter == self.game_counter:
                    reader: asyncio.StreamReader = client[READER]
                    chars = (await reader.read(1)).decode()
                    if len(chars) == 0:
                        raise asyncio.CancelledError()
                    client[COUNTER] += len(chars)
            except Exception:
                return
        
        async def close_client_conn(client, msg):
            try:
                client[WRITER].write(msg.encode())
                await client[WRITER].drain()
                client[WRITER].close()
                asyncio.create_task(client[WRITER].wait_closed())
            except Exception:
                return
    
        start_game_msg = self.game_data_message()
        print(start_game_msg)
        tasks = []
        # create a coroutine for reading chars from each client 
        for client in self.clients:
            tasks.append(asyncio.create_task(make_client_listener(client, self.game_counter, start_game_msg)))
        # let them run for GAME_TIME seconds
        await asyncio.sleep(config.GAME_TIME)
        # close the coroutines
        for task in tasks:
            if not task.cancelled():
                task.cancel()
        end_msg = self.end_game_message()
        print(end_msg)
        # create a task for sending an ending message and closing the connection for every client
        for client in self.clients:
            asyncio.create_task(close_client_conn(client, end_msg))
        
        # end game
        
    def game_data_message(self):
        # generate a game description message
        msg = "Welcome to Keyboard Spamming Battle Royale.\nGroup 1:\n==\n"
        for name in self.group_1:
            msg += name + "\n"
        msg += "\nGroup 2:\n==\n"
        for name in self.group_2:
            msg += name + "\n"
        msg += "\nStart pressing keys on your keyboard as fast as you can!!\n"
        return msg

    def end_game_message(self):
        # generate a sum up message
        sum_1 = 0
        sum_2 = 0
        best_count = 0
        best_name = None
        for client in self.clients:
            if client[COUNTER] > best_count:
                best_count = client[COUNTER]
                best_name = client[NAME]
            if client[GROUP] == 1:
                sum_1 += client[COUNTER]
            else:
                sum_2 += client[COUNTER]
        msg = f"{Colors.HEADER}Game over!\n{Colors.OKBLUE}Group 1 typed in {str(sum_1)} characters. Group 2 typed in {str(sum_2)} characters.\n"
        if sum_1 > sum_2:
            msg += f"{Colors.OKGREEN}Group 1 wins!\nCongratulations to the winners:\n==\n"
            for name in self.group_1:
                msg += Colors.BOLD + name + "\n"
        elif sum_1 < sum_2:
            msg += f"{Colors.OKGREEN}Group 2 wins!\nCongratulations to the winners:\n==\n"
            for name in self.group_2:
                msg += Colors.BOLD + name + "\n"
        else:
            msg += f"{Colors.OKCYAN}It's a Tie!\n"
        msg += f"{Colors.BOLD}The best player is {best_name} !!!\n" if best_name else "No best player :("
        return (msg + Colors.ENDC)

    def clean_up(self):
        self.clients.clear()
        self.group_1.clear()
        self.group_2.clear()
        self.game_counter += 1
        self.state = ServerState.SENDING_INVITES
      
    async def send_invites(self):
        i = 0
        while True:
            if i == config.INVITES_TIME:
                # start ame
                self.state = ServerState.IN_GAME
                await self.make_game()
                self.clean_up()
                i = 0
            if self.state == ServerState.SENDING_INVITES: 
                # send invite in tcp
                self.udp_socket.sendto(self.invite, (config.BROADCAST_IP if config.DEBUG else config.BROADCAST_IP, config.INVITES_PORT))
                await asyncio.sleep(1)
                i += 1

    def add_connection(self):
        async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            if self.state == ServerState.SENDING_INVITES:
                addr = writer.get_extra_info('peername')
                # check if we want to connect to this client (debuging purposes)
                if config.DEBUG and addr[0] not in config.EXCLUSIVE_IPS:
                    return
                # get client name
                client_name = (await reader.read(config.READ_BUFFER)).decode()
                new_line_idx = client_name.find('\n')
                if new_line_idx != -1:
                    client_name = client_name[:new_line_idx]
                # group client
                group = random.randint(1, 2)
                self.clients.append([client_name, addr, reader, writer, 0, group])
                if group == 1:
                    self.group_1.append(client_name)
                else:
                    self.group_2.append(client_name)

        return handle_connection 
        
    async def start(self):
        print(f"Server started, listening on IP address {config.MY_IP}")
        self.server = await asyncio.start_server(self.add_connection(), self.ip_address, config.SERVER_TCP_PORT)
        asyncio.create_task(self.send_invites())
        async with self.server:
            await self.server.serve_forever()
        
        
def main():
    server = Server()
    asyncio.run(server.start())

if __name__ == "__main__":
    main()