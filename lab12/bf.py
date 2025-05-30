import time
import socket
import threading
import random


global_network_version = 0
RealAddress = tuple[str, int]

server_host = '127.0.0.1'
server_port = 20000
server_address = (server_host, server_port)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(server_address)


def ip_encode(ip: str):
    return bytes(list(map(int, ip.split('.'))))


def ip_decode(ip_encoded: bytes):
    return '.'.join(map(str, ip_encoded))


def int_encode(integer: int, n_bytes: bytes):
    return bytes([(integer // (0x100 ** i)) % 0x100 for i in range(n_bytes)])


def int_decode(data: bytes):
    return sum([data[i] * (0x100 ** i) for i in range(len(data))])


def random_ip():
    return '.'.join(map(str, (random.randint(0x00, 0xff) for _ in range(4))))


def router_routine(ip: str):
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    neighbours: dict[RealAddress, str] = {}
    path_to_other: dict[str, tuple[str, int]] = {}  # dest router -> (next hop, metric)

    # first, all routers send their identification to server
    my_socket.sendto(b'HELO' + ip_encode(ip), server_address)

    while True:
        data, raddr = my_socket.recvfrom(256)
        if raddr == server_address:
            # message from the server
            if data[:4] == b'CNCT':
                # connect to another router using real socket address
                neighbour_ip = ip_decode(data[4:8])
                neighbour_realhost = ip_decode(data[8:12])
                neighbour_realport = int_decode(data[12:14])
                
                neighbours[(neighbour_realhost, neighbour_realport)] = neighbour_ip
                path_to_other[neighbour_ip] = (neighbour_ip, 1)
            elif data[:4] == b'BDCS':
                # broadcast to all
                for neighbour_ip in neighbours.values():
                    for another_neighbour_raddr, another_neighbour_ip in neighbours.items():
                        if another_neighbour_ip == neighbour_ip:
                            continue
                        my_socket.sendto(b'DIST' + ip_encode(ip) + ip_encode(neighbour_ip) + int_encode(path_to_other[neighbour_ip][1], 1), another_neighbour_raddr)
            elif data[:4] == b'REQU':
                # request for distance to other router
                dest_router_ip = ip_decode(data[4:8])
                if dest_router_ip not in path_to_other:
                    my_socket.sendto(b'RESP' + ip_encode('0.0.0.0') + int_encode(16, 1), server_address)
                else:
                    next_hop, metric = path_to_other[dest_router_ip]
                    my_socket.sendto(b'RESP' + ip_encode(next_hop) + int_encode(metric, 1), server_address)
            elif data[:4] == b'QUIT':
                my_socket.close()
                return
            else:
                raise AssertionError(f'unknown message type: {data[:4]}')
        else:
            # message from a neighbour
            assert data[:4] == b'DIST', str(data[:4])
            neighbour_ip = neighbours[raddr]
            assert ip_decode(data[4:8]) == neighbour_ip, f'{ip_decode(data[4:8])} != {neighbour_ip}'

            dest_router_ip = ip_decode(data[8:12])
            metric = int_decode(data[12:13])

            if dest_router_ip not in path_to_other or \
                    path_to_other[dest_router_ip][1] > metric + 1:
                path_to_other[dest_router_ip] = (neighbour_ip, metric + 1)
                # broadcast
                for another_neighbour_raddr, another_neighbour_ip in neighbours.items():
                    if another_neighbour_ip == neighbour_ip:
                        continue
                    my_socket.sendto(b'DIST' + ip_encode(ip) + ip_encode(dest_router_ip) + int_encode(metric + 1, 1), another_neighbour_raddr)
            


N_ROUTERS = random.randint(4, 10)
N_CHANNELS = random.randint(N_ROUTERS // 2, min(N_ROUTERS * 2, N_ROUTERS * (N_ROUTERS - 1) // 2))

if __name__ == '__main__':
    # generate routers
    router_ips = [random_ip() for _ in range(N_ROUTERS)]
    router_threads = [threading.Thread(target=router_routine, name=router_ips[i], args=(router_ips[i],)) for i in range(N_ROUTERS)]
    for th in router_threads:
        th.start()

    # server waits for all routers to respond
    router_realaddrs = [None] * N_ROUTERS
    for _ in range(N_ROUTERS):
        router_data, router_address = server_socket.recvfrom(256)
        assert router_data[:4] == b'HELO', str(router_data[:4])
        router_ip = ip_decode(router_data[4:])
        for i in range(N_ROUTERS):
            if router_ip == router_ips[i]:
                router_realaddrs[i] = router_address
                break
        else:
            raise AssertionError(f'router IP {router_ip} not found')
        

    # generate channels
    connected_pairs = set()
    edges_for_visualization = []
    for _ in range(N_CHANNELS):
        while True:
            src_router_id = random.randint(0, N_ROUTERS-1)
            dst_router_id = random.randint(0, N_ROUTERS-1)

            if src_router_id != dst_router_id and \
                    (src_router_id, dst_router_id) not in connected_pairs:
                # send a connection message
                src_router_ip = router_ips[src_router_id]
                dst_router_ip = router_ips[dst_router_id]
                src_router_raddr = router_realaddrs[src_router_id]
                dst_router_raddr = router_realaddrs[dst_router_id]

                server_socket.sendto(b'CNCT' + ip_encode(dst_router_ip) + ip_encode(dst_router_raddr[0]) + int_encode(dst_router_raddr[1], 2), src_router_raddr)
                server_socket.sendto(b'CNCT' + ip_encode(src_router_ip) + ip_encode(src_router_raddr[0]) + int_encode(src_router_raddr[1], 2), dst_router_raddr)
                
                connected_pairs.add((src_router_id, dst_router_id))
                connected_pairs.add((dst_router_id, src_router_id))
                edges_for_visualization.append((min(src_router_id, dst_router_id), max(src_router_id, dst_router_id)))
                break
    
    # visualize network
    print('Network visualization:')
    for edge in edges_for_visualization:
        print(f'{router_ips[edge[0]].rjust(15)}----{router_ips[edge[1]]}')
    
    print('Broadcasting...')
    # send broadcast commands
    for i in range(N_ROUTERS):
        router_raddr = router_realaddrs[i]
        server_socket.sendto(b'BDCS', router_raddr)
    
    # wait for 4s
    time.sleep(4)

    # output the final table
    for ri in range(N_ROUTERS):
        print(f'Final state of router {router_ips[ri]} table:')
        print('[Source IP]      [Destination IP]    [Next Hop]       [Metric]  ')
        for rj in range(N_ROUTERS):
            if ri == rj:
                continue

            server_socket.sendto(b'REQU' + ip_encode(router_ips[rj]), router_realaddrs[ri])
            data, raddr = server_socket.recvfrom(256)
            assert raddr == router_realaddrs[ri]
            assert data[:4] == b'RESP'
            next_hop = ip_decode(data[4:8])
            metric = int_decode(data[8:9])

            print(f'{router_ips[ri].ljust(17)}{router_ips[rj].ljust(20)}{next_hop.ljust(17) if metric != 16 else '-'.ljust(17)}{str(metric).rjust(8)}')
        print()

    # quit
    for i in range(N_ROUTERS):
        server_socket.sendto(b'QUIT', router_realaddrs[i])


        

'''
class Router:  # a.k.a. node
    def __init__(self, ip_address: str):
        

    def broadcast(self, message: Message):
        for channel in self.channels:
            if channel.other_end(self) != message.dest_router:
                channel.other_end(self).accept_message(message)
    
    def accept_message(self, message: Message):
        for channel in self.channels:
            neighbour = channel.other_end(self)

            # DEBUG
            #print(f'% {self.id} {neighbour.id} {message.src_router.id} {message.dest_router.id} {message.path_cost}')

            if neighbour == message.src_router:
                old_path = self.path_to_other.get(message.dest_router, None)
                if old_path is None or \
                        message.version > old_path[2] or \
                        channel.cost + message.path_cost < old_path[1]:
                    self.path_to_other[message.dest_router] = (neighbour, channel.cost + message.path_cost, message.version)
                    self.broadcast(Message(self, message.dest_router, channel.cost + message.path_cost, message.version))
                break


class Channel:  # a.k.a. edge
    def __init__(self, start: Router, end: Router, cost: int):
        self.start = start
        self.end = end
        self.cost = cost
    
    def other_end(self, router: Router):
        if router == self.start:
            return self.end
        elif router == self.end:
            return self.start
        else:
            raise ValueError(f'channel {self.start.id}--{self.end.id} is not adjacent to router {router.id}')
        
    def change_cost(self, new_cost: int):
        self.cost = new_cost


def connect(router1: Router, router2: Router, cost: int) -> Channel:
    channel = Channel(router1, router2, cost)
    router1.channels.append(channel)
    router2.channels.append(channel)
    return channel


def broadcast_all(routers: list[Router]):
    global global_network_version
    
    global_network_version += 1
    for router in routers:
        for channel in router.channels:
            neighbour = channel.other_end(router)
            if router.path_to_other.get(neighbour) is None or \
                    router.path_to_other[neighbour][2] < global_network_version or \
                    router.path_to_other[neighbour][1] > channel.cost:
                router.path_to_other[neighbour] = (neighbour, channel.cost, global_network_version)

            router.broadcast(Message(router, channel.other_end(router), channel.cost, global_network_version))


def output_dist_table(routers: list[Router], cell_width: int=4):
    print(' ' * cell_width + '|' + '|'.join(map(lambda router: str(router.id).rjust(cell_width), routers)))
    print('-' * cell_width + '+' + '-' * (cell_width * len(routers)))
    
    for ri in routers:
        print(str(ri.id).rjust(cell_width), end='')
        for rj in routers:
            print('|' + str(rj.path_to_other.get(ri, (None, None))[1]).rjust(cell_width), end='')
        print()


if __name__ == '__main__':
    router0 = Router(0)
    router1 = Router(1)
    router2 = Router(2)
    router3 = Router(3)

    channel01 = connect(router0, router1, 1)
    channel12 = connect(router1, router2, 1)
    channel02 = connect(router0, router2, 3)
    channel03 = connect(router0, router3, 7)
    channel32 = connect(router3, router2, 2)

    routers = [router0, router1, router2, router3]
    broadcast_all(routers)

    print('Initial Distance Table:')
    output_dist_table(routers)

    print('Changing the cost of 0-1 channel to 3')
    channel01.change_cost(3)
    broadcast_all(routers)

    print('New Distance Table:')
    output_dist_table(routers)

    print('Changing the cost of 0-3 channel to 1')
    channel03.change_cost(1)
    broadcast_all(routers)

    print('New Distance Table:')
    output_dist_table(routers)
'''