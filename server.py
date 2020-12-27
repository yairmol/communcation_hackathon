import config
import socket
from struct import pack, unpack
import asyncio
from enum import Enum, auto


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
        self.server = None

    def make_game(self):
        pass

    async def send_invites(self):
        i = 0
        while True:
            if i == 10:
                self.state = ServerState.IN_GAME
                i = 0
                await asyncio.sleep(10)
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
                self.clients.append((client_name, addr, reader, writer, 0))
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