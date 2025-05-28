import checksum
import random


def good_test_1():
    data = b'Hello World!'
    chksum = (-1 - (sum(b'HloWrd') + sum(b'el ol!') * 0x100)) % (1 << 16)
    return checksum.verify_checksum(data, chksum)


def good_test_2():
    rand = random.Random(19283)
    even = [rand.randint(0x00, 0xff) for _ in range(100000)]
    odd  = [rand.randint(0x00, 0xff) for _ in range(100000)]
    data = bytes([b for eo in zip(even, odd) for b in eo])
    chksum = (-1 - (sum(even) + sum(odd) * 0x100)) % (1 << 16)
    return checksum.verify_checksum(data, chksum)


def good_test_3():
    data = b'I was not expecting that. But I was expecting not to expect something so it doesn\'t count.'
    return checksum.verify_checksum(data, checksum.get_checksum(data))


def bad_test_1():
    data = b'Hello World!'
    chksum = (-1 - (sum(b'HloWrd') + sum(b'el ol!') * 0x100)) % (1 << 16)
    chksum -= 1
    return not checksum.verify_checksum(data, chksum)


def bad_test_2():
    rand = random.Random(19284)
    even = [rand.randint(0x00, 0xff) for _ in range(100000)]
    odd  = [rand.randint(0x00, 0xff) for _ in range(100000)]
    data = bytes([b for eo in zip(even, odd) for b in eo])
    data = data[:5] + bytes([0xff - data[5]]) + data[6:]
    chksum = (-1 - (sum(even) + sum(odd) * 0x100)) % (1 << 16)
    return not checksum.verify_checksum(data, chksum)


def bad_test_3():
    data = b'All your base are belong to us.'
    chksum = checksum.get_checksum(data)
    data = data[:10] + bytes([0xC]) + data[10:]
    return not checksum.verify_checksum(data, chksum)


if __name__ == '__main__':
    for test in [good_test_1, good_test_2, good_test_3, bad_test_1, bad_test_2, bad_test_3]:
        print(f'{test.__name__}: {"ok" if test() else "FAILED"}')