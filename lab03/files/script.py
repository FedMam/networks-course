import random

N = 1024 ** 2 * 10
with open('secret_data.bin', 'wb') as file:
    file.write(bytearray((random.randint(0x00, 0xff) for _ in range(N))))
