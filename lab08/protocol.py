import socket
import random
import io
import math
import checksum


def _corrupt(data: bytes, rand: random.Random):
    for i in range(min(math.ceil(len(data) / 10), 5)):
        index = rand.randint(0, len(data)-1)
        data = data[:index] + bytes([rand.randint(0x00, 0xff)]) + data[index+1:]
    return data


class Sender:
    def __init__(self,
                 sock: socket.socket,
                 chunk_size: int=1024,
                 timeout: float=1.0,
                 loss_prob: float=0.3,
                 corrupt_prob: float=0.1,
                 seed: int=None):
        self.sock = sock
        self.sock.settimeout(timeout)
        self.chunk_size = chunk_size
        self.loss_prob = loss_prob
        self.corrupt_prob = corrupt_prob
        self.rand = random.Random(seed)

        print('Sender initialized')
    
    def send(self, buffer: io.BufferedReader, address: tuple[str, int]):
        segment_ctr = 0
        sequence_bit = 0
        fin = False

        print(f'Sending file to {address[0]}:{address[1]}')

        while True:
            data = buffer.read(self.chunk_size-3)
            if not data:
                data = b'FIN' # final message
                fin = True
            data = bytes([sequence_bit]) + data

            print(f'Sending ' + (f'data chunk {segment_ctr}' if not fin else 'FIN') + f', sequence number: {sequence_bit}')

            chksum = checksum.get_checksum(data)
            data += bytes([chksum % 0x100, chksum // 0x100])
            
            while True:
                if self.rand.random() < self.loss_prob:
                    print('Oops, data chunk lost :(')
                elif self.rand.random() < self.corrupt_prob:
                    corrupt_data = _corrupt(data, self.rand)
                    self.sock.sendto(corrupt_data, address)
                    print('Successfully sen...oh no, I think I\'ve sent corrupted data.')
                else:
                    self.sock.sendto(data, address)
                    print('Successfully sent')
                
                # ack recv
                # ack format: b'\0ACK' or b'\1ACK'
                try:
                    ack, address = self.sock.recvfrom(256)

                    if not checksum.verify_checksum(ack[:-2], ack[-2] + ack[-1] * 0x100):
                        print('ACK checksum failed')
                    else:
                        if address == address and \
                        ack[0] == sequence_bit and \
                        ack[1:-2] == b'ACK':
                            # ack received
                            print('ACK received')
                            break
                        elif ack[0] != sequence_bit:
                            print(f'Incorrect ACK sequence number: {ack[0]}')
                        else:
                            print('Incorrect ACK format')
                except socket.timeout:
                    # timeout
                    print('Timeout waiting for ACK')
                    pass
            
            sequence_bit = 1 - sequence_bit
            segment_ctr += 1

            if fin:
                break
        
        print('Successfully sent file!')


class Receiver:
    def __init__(self,
                 sock: socket.socket,
                 loss_prob: float=0.3,
                 corrupt_prob: float=0.1,
                 buffer_size: int=1024,
                 final_timeout: float=10.0,
                 seed: int=None):
        self.sock = sock
        self.loss_prob = loss_prob
        self.corrupt_prob = corrupt_prob
        self.rand = random.Random(seed)
        self.buffer_size = buffer_size
        self.final_timeout = final_timeout

        print('Receiver initialized')
    
    def receive(self) -> tuple[bytes, tuple[str, int]]:
        self.sock.settimeout(None)
        segment_ctr = 0
        fin = False
        received_data = b''
        sender_address = None
        sequence_bit = 0

        print('Ready to receive')

        while True:
            try:
                data, address = self.sock.recvfrom(self.buffer_size)
            except socket.timeout:
                # timeout is set only after receiving FIN
                # consider finished
                break
            
            if sender_address is None:
                sender_address = address
            if address != sender_address:
                print('Wrong address')
                continue

            if not checksum.verify_checksum(data[:-2], data[-2] + data[-1] * 0x100):
                print(f'Data checksum failed')
                continue

            if data[0] != sequence_bit:
                # discard duplicate frame
                print(f'Incorrect sequence number: {data[0]}')
            else:
                if data[1:-2] == b'FIN':
                    fin = True
                    print('Received FIN')
                else:
                    print(f'Received data chunk {segment_ctr}, sequence number {sequence_bit}')
                    received_data += data[1:-2]
                segment_ctr += 1
                sequence_bit = 1 - sequence_bit
            
            ack = bytes([1 - sequence_bit]) + b'ACK'
            chksum = checksum.get_checksum(ack)
            ack += bytes([chksum % 0x100, chksum // 0x100])

            if self.rand.random() < self.loss_prob:
                print('Oops, ACK lost :(')
            elif self.rand.random() < self.corrupt_prob:
                ack = _corrupt(ack, self.rand)
                self.sock.sendto(ack, address)
                print('Oh no, I\'ve sent corrupted ACK  \\(˚☐˚”)/')
            else:
                # sequence bit is inverted here because it equals the
                # sequence bit of the last received frame instead of
                # the next expected frame
                self.sock.sendto(ack, address)
                print('ACK sent')

            if fin:
                self.sock.settimeout(self.final_timeout)
        
        print('Successfully received file!')
        return received_data, sender_address

