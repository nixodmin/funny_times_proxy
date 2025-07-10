import socket
import threading
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
import struct
import select

PASSWORD = "mysecretpassword"
SERVER_IP = "your-server-ip"
SERVER_PORT = 8388
BUFFER_SIZE = 16384
TIMEOUT = 30

def pack_target(addr, port):
    addr_bytes = addr.encode()
    return struct.pack('!IH', len(addr_bytes), port) + addr_bytes

def handle_socks5(client_sock):
    try:
        version = client_sock.recv(1)
        if version != b"\x05":
            return None
        
        nmethods = client_sock.recv(1)[0]
        methods = client_sock.recv(nmethods)
        if 0x00 not in methods:
            client_sock.sendall(b"\x05\xFF")
            return None
        
        client_sock.sendall(b"\x05\x00")

        data = client_sock.recv(4)
        if len(data) < 4:
            return None
        
        version, cmd, _, addr_type = data
        if version != 5 or cmd != 1:
            return None
        
        if addr_type == 1:
            addr = socket.inet_ntoa(client_sock.recv(4))
        elif addr_type == 3:
            domain_length = client_sock.recv(1)[0]
            addr = client_sock.recv(domain_length).decode()
        else:
            return None
        
        port = int.from_bytes(client_sock.recv(2), "big")
        client_sock.sendall(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
        return addr, port
    except:
        return None

def forward_traffic(client_sock, target_addr, target_port):
    key = SHA256.new(PASSWORD.encode()).digest()
    iv = get_random_bytes(16)
    remote_sock = None
    
    try:
        remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_sock.settimeout(TIMEOUT)
        remote_sock.connect((SERVER_IP, SERVER_PORT))

        # Отправляем IV
        remote_sock.sendall(iv)
        
        # Создаем отдельные cipher объекты
        encrypt_cipher = AES.new(key, AES.MODE_CFB, iv=iv)
        decrypt_cipher = AES.new(key, AES.MODE_CFB, iv=iv)

        # Отправляем целевой адрес
        target_data = pack_target(target_addr, target_port)
        remote_sock.sendall(encrypt_cipher.encrypt(target_data))

        while True:
            rlist, _, _ = select.select([client_sock, remote_sock], [], [], TIMEOUT)
            
            for sock in rlist:
                try:
                    if sock is client_sock:
                        data = client_sock.recv(BUFFER_SIZE)
                        if not data:
                            return
                        encrypted = encrypt_cipher.encrypt(data)
                        remote_sock.sendall(encrypted)
                    else:
                        data = remote_sock.recv(BUFFER_SIZE)
                        if not data:
                            return
                        decrypted = decrypt_cipher.decrypt(data)
                        client_sock.sendall(decrypted)
                except (socket.timeout, ConnectionResetError):
                    continue

    except Exception as e:
        print(f"Forward error: {e}")
    finally:
        if remote_sock:
            remote_sock.close()
        client_sock.close()

def start_proxy():
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy.bind(("127.0.0.1", 1080))
    proxy.listen(5)
    print("SOCKS5 proxy running on 127.0.0.1:1080")

    try:
        while True:
            client_sock, addr = proxy.accept()
            client_sock.settimeout(TIMEOUT)
            print(f"New connection from {addr}")
            target = handle_socks5(client_sock)
            if target:
                threading.Thread(target=forward_traffic, args=(client_sock, *target)).start()
            else:
                client_sock.close()
    except KeyboardInterrupt:
        print("\nShutting down proxy...")
    finally:
        proxy.close()

if __name__ == "__main__":
    start_proxy()
