def _sum_shorts(data: bytes):
    short_sum = 0

    for i in range((len(data) + 1) // 2):
        short_sum += data[2*i] + ((data[2*i+1] if (2*i < len(data)-1) else 0) << 8)
        short_sum %= (1 << 16)
    
    return short_sum


def get_checksum(data: bytes):
    return ((1 << 16) - 1) - _sum_shorts(data)  # bitwise not


def verify_checksum(data: bytes, checksum: int):
    return _sum_shorts(data) + checksum == ((1 << 16) - 1)