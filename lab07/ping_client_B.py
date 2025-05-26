import socket
import time


host = '127.0.0.1'
port = 19288

client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

lost = 0
global_start_time = time.time()
rtt_data = []

try:
    for i in range(1, 10+1):
        start_time = time.time()
        client_sock.settimeout(1.0)
        msg = f'Ping {i} {start_time}'
        client_sock.sendto(msg.encode(), (host, port))
        try:
            resp, addr = client_sock.recvfrom(1024)
            end_time = time.time()
            rtt = end_time - start_time
            rtt_data.append(rtt * 1000)
            print(f'{len(resp)} bytes from {host}: icmp_seq={i} time={rtt * 1000:.3f} ms')
        except socket.timeout:
            print('request timed out')
            lost += 1
    
    global_end_time = time.time()
    print(f'--- {host} ping statistics ---')
    print(f'10 packets transmitted, {10 - lost} received, {lost * 10}% packet loss, time {int((global_end_time - global_start_time) * 1000)}ms')
    
    rtt_avg = sum(rtt_data) / len(rtt_data)
    print(f'rtt min/avg/max/mdev: {min(rtt_data):.3f}/{rtt_avg:.3f}/{max(rtt_data):.3f}/{sum([abs(it - rtt_avg) for it in rtt_data])/len(rtt_data):.3f}')
except Exception as E:
    print(f'error: {E}')
finally:
    client_sock.close()