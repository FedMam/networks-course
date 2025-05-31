from scapy.all import sniff, get_if_addr, get_if_list

in_traffic = 0
out_traffic = 0
in_traffic_by_port = {}
out_traffic_by_port = {}

my_ips = list(map(get_if_addr, get_if_list()))

def packet_callback(packet):
    global in_traffic, out_traffic

    if packet.haslayer('IP'):
        if packet['IP'].dst in my_ips:
            # incoming packet

            in_traffic += len(packet)

            port = None
            if packet.haslayer('TCP'):
                port = packet['TCP'].dport
            if packet.haslayer('UDP'):
                port = packet['UDP'].dport
            
            if port is not None:
                in_traffic_by_port[port] = in_traffic_by_port.get(port, 0) + len(packet)

        elif packet['IP'].src in my_ips:
            # outgoing packet

            out_traffic += len(packet)

            port = None
            if packet.haslayer('TCP'):
                port = packet['TCP'].sport
            if packet.haslayer('UDP'):
                port = packet['UDP'].sport
            
            if port is not None:
                out_traffic_by_port[port] = out_traffic_by_port.get(port, 0) + len(packet)

try:
    print('Sniffing started, press Ctrl+C to terminate')
    sniff(prn=packet_callback, store=0)
except KeyboardInterrupt:
    pass

print()
# output stats
print(f'Incoming traffic: {in_traffic} bytes')
print(f'Outgoing traffic: {out_traffic} bytes')
print()
print('Incoming traffic by port:')
for port in sorted(in_traffic_by_port.keys()):
    print(f'{port}: {in_traffic_by_port[port]} bytes')
print()
print('Outgoing traffic by port:')
for port in sorted(out_traffic_by_port.keys()):
    print(f'{port}: {out_traffic_by_port[port]} bytes')
