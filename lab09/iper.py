import socket
import psutil

interfaces = psutil.net_if_addrs()
for i_name, addresses in interfaces.items():
    for address in addresses:
        if address.family == socket.AF_INET:
            ip = address.address
            netmask = address.netmask

            print(f"Interface: {i_name}")
            print(f"Address: {ip}")
            print(f"Netmask: {netmask}")
            print()