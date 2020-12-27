import sys
import scapy.all as scapy

DEVLOPMENT_NET = "eth1"
TEST_NET = "eth2"

CURRENT_NET = sys.argv[1] if len(sys.argv) > 1 else DEVLOPMENT_NET
MY_IP = scapy.get_if_addr(CURRENT_NET)

INVITES_PORT = 13117
DEBUG = True