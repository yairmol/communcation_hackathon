import sys
import scapy.all as scapy

OUR_NAME = "RICK ACKSTLY https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstleyVEVO"

# network config
DEVLOPMENT_NET = "eth1"
TEST_NET = "eth2"
CURRENT_NET = sys.argv[1] if len(sys.argv) > 1 else DEVLOPMENT_NET
CURRENT_NET = scapy.conf.iface if CURRENT_NET == "local" else CURRENT_NET
MY_IP = scapy.get_if_addr(CURRENT_NET)
print(CURRENT_NET, MY_IP)
BROADCAST_IP = '255.255.255.255' if CURRENT_NET not in [DEVLOPMENT_NET, TEST_NET] else '172.1.255.255'
INVITES_PORT = 13117
SERVER_TCP_PORT = 2077

# game config
INVITES_TIME = 10
GAME_TIME = 10

# utils
MAGIC_COOKIE = 0xfeedbeef
FLAG = 2
READ_BUFFER = 2048
PACKING_FORMAT = "!IbH"

# debug config
EXCLUSIVE_IPS = ['172.1.0.77', '172.1.0.117']
DEBUG = False