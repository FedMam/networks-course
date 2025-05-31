import crc
import random
import math
import os
import sys


def invert_random_bit(data: bytes, rand: random.Random):
    byte_i = rand.randint(0, len(data)-1)
    bit_i = rand.randint(0, 7)
    return data[:byte_i] + bytes([data[byte_i] ^ (1 << bit_i)]) + data[byte_i+1:]


def test_1():
    data = b'All your base are belong to us'
    chksum = crc.crc_get_chksum(data)
    data += bytes([chksum])

    return crc.crc_check(data)


def test_1_star():
    data = 'Съешь ещё этих мягких французских булок, да выпей чаю'.encode('utf-8')
    chksum = crc.crc_get_chksum(data)
    data += bytes([chksum])

    return crc.crc_check(data)


def test_2():
    data = b'Change my mind'
    chksum = crc.crc_get_chksum(data)
    data += bytes([chksum])

    rand = random.Random(19283)
    for i in range(5):
        data = invert_random_bit(data, rand)
    return not crc.crc_check(data)


def test_3():
    data = b'This is fine'
    chksum = crc.crc_get_chksum(data)
    data += bytes([chksum])

    rand = random.Random(19284)
    data = invert_random_bit(data, rand)
    return not crc.crc_check(data)


def test_4():
    data = b'All your base are belong to us'
    chksum = crc.crc_get_chksum(data)
    data += bytes([chksum])

    data = data[:10] + bytes([0xff - data[10]]) + data[11:]
    return not crc.crc_check(data)


def main():
    rand = random.Random()

    files_dir = os.path.dirname(os.path.abspath(sys.argv[0])) + '/files/'
    filename = input('>>> Filename: ')

    try:
        with open(files_dir + filename, 'r') as file:
            text = file.read()
    except OSError as E:
        print(f'Cannot open file: {E}')
        return -1
    
    print('Initial text:')
    print()
    print(text)
    print()
    print('Sending...')

    data = text.encode('utf-8')
    received_data = b''

    for i in range(math.ceil(len(data) / 5)):
        while True:
            chunk = data[5 * i: min(len(data), 5 * i + 5)]
            chksum = crc.crc_get_chksum(chunk)
            chunk += bytes([chksum])

            if rand.random() < 0.1:
                # corrupt chunk
                for j in range(rand.randint(1, 5)):
                    chunk = invert_random_bit(chunk, rand)
            
            print(f'Sending chunk: {chunk}, payload: {chunk[:-1]}, checksum: {chunk[-1]} ({hex(chunk[-1])}{(", '" + chr(chunk[-1]) + "'") if 0x20 <= chunk[-1] <= 0x7E else ""})')
                
            if crc.crc_check(chunk):
                print(f'Chunk OK')
                received_data += chunk[:-1]
                break
            else:
                print(f'Chunk CORRUPTED, resend!')
    
    if data == received_data:
        print('Successfully sent, received data not corrupted!')
    else:
        print('Oh no, received data has been corrupted!')
        print('Received text:')
        print()
        try:
            print(received_data.decode('utf-8'))
        except Exception as E:
            print(received_data)
        print()


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'main'

    if mode == 'test' or mode == 'tests':
        for test in [test_1, test_1_star, test_2, test_3, test_4]:
            print(f'{test.__name__}: {"ok" if test() else "FAILED"}')
    else:
        main()