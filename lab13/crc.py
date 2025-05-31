def bytes_to_bitstring(bts: bytes):
    bitstr = []
    for b in bts:
        for i in range(7, -1, -1):
            bitstr.append(1 if (b & (1 << i)) != 0 else 0)
    return bitstr


def bitstring_to_bytes(bitstr: list[int]):
    if len(bitstr) % 8 != 0:
        raise ValueError(f'incorrect bitstring of length {len(bitstr)}: {"".join(map(str, bitstr))}')

    bit_i = 7
    bts = []
    curr = 0
    for bit in bitstr:
        if bit == 1:
            curr += (1 << bit_i)
        
        if bit_i == 0:
            bit_i = 7
            bts.append(curr)
            curr = 0
        else:
            bit_i -= 1
    
    return bytes(bts)


# CRC-8-DVB-S2
divisor = 0xd5

def _crc_calc(data: bytes):
    crc_curr = 0
    bitstr = bytes_to_bitstring(data)

    for b in bitstr:
        if (crc_curr & (0x80)) != 0:
            crc_curr = (((crc_curr << 1) + b) & 0xff) ^ divisor
        else:
            crc_curr = (((crc_curr << 1) + b) & 0xff)
    
    return crc_curr


def crc_get_chksum(data: bytes):
    data = data + bytes([0])
    return _crc_calc(data)


def crc_check(data: bytes):
    # the last byte of data is the checksum
    return _crc_calc(data) == 0