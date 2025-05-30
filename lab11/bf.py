global_network_version = -1


class Message:
    def __init__(self, src_router: 'Router', dest_router: 'Router', path_cost: int, version: int):
        # a router must discard information with older version than the message's
        self.src_router = src_router
        self.dest_router = dest_router
        self.path_cost = path_cost
        self.version = version


class Router:  # a.k.a. node
    def __init__(self, id: int):
        self.id = id
        self.channels: list[Channel] = []
        self.path_to_other: dict[Router, tuple[int, int]] = {}  # dest.router -> (path cost, version)
        self.path_to_other[self] = (0, 10 ** 9)

    def broadcast(self, message: Message):
        for channel in self.channels:
            channel.other_end(self).accept_message(message)
    
    def accept_message(self, message: Message):
        for channel in self.channels:
            neighbour = channel.other_end(self)

            # DEBUG
            #print(f'% {self.id} {neighbour.id} {message.src_router.id} {message.dest_router.id} {message.path_cost}')

            if neighbour == message.src_router:
                old_path = self.path_to_other.get(message.dest_router, None)
                if old_path is None or \
                        message.version > old_path[1] or \
                        (message.version == old_path[1] and channel.cost + message.path_cost < old_path[0]):
                    self.path_to_other[message.dest_router] = (channel.cost + message.path_cost, message.version)
                    self.broadcast(Message(self, message.dest_router, *self.path_to_other[message.dest_router]))
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
        router.broadcast(Message(router, router, 0, global_network_version))


def output_dist_table(routers: list[Router], cell_width: int=4):
    print(' ' * cell_width + '|' + '|'.join(map(lambda router: str(router.id).rjust(cell_width), routers)))
    print('-' * cell_width + '+' + '-' * (cell_width * len(routers)))
    
    for ri in routers:
        print(str(ri.id).rjust(cell_width), end='')
        for rj in routers:
            print('|' + str(rj.path_to_other.get(ri, (None, None))[0]).rjust(cell_width), end='')
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