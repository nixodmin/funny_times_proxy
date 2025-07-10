import socket
import threading
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
import struct
import select

PASSWORD = "mysecretpassword"
BUFFER_SIZE = 16384

def handle_client(client_sock):
    remote_sock = None
    try:
        # Получаем IV (16 байт)
        iv = client_sock.recv(16)
        if len(iv) != 16:
            print("Invalid IV length")
            return

        # Генерируем ключ
        key = SHA256.new(PASSWORD.encode()).digest()
        
        # Создаем РАЗНЫЕ объекты для шифрования и дешифрования
        decrypt_cipher = AES.new(key, AES.MODE_CFB, iv=iv)
        encrypt_cipher = AES.new(key, AES.MODE_CFB, iv=iv)

        # Получаем длину адреса и порт
        encrypted_header = client_sock.recv(6)
        if len(encrypted_header) != 6:
            print("Invalid header length")
            return

        header = decrypt_cipher.decrypt(encrypted_header)
        addr_len, port = struct.unpack('!IH', header)

        # Получаем сам адрес
        encrypted_addr = client_sock.recv(addr_len)
        if len(encrypted_addr) != addr_len:
            print("Invalid address length")
            return

        remote_addr = decrypt_cipher.decrypt(encrypted_addr).decode()
        print(f"Connecting to {remote_addr}:{port}")

        # Подключаемся к целевому серверу
        remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_sock.settimeout(30)
        remote_sock.connect((remote_addr, port))
        print("Connection established")

        # Туннелируем данные
        while True:
            rlist, _, _ = select.select([client_sock, remote_sock], [], [], 60)
            
            for sock in rlist:
                try:
                    if sock is client_sock:
                        data = client_sock.recv(BUFFER_SIZE)
                        if not data:
                            return
                        decrypted = decrypt_cipher.decrypt(data)
                        remote_sock.sendall(decrypted)
                    else:
                        data = remote_sock.recv(BUFFER_SIZE)
                        if not data:
                            return
                        encrypted = encrypt_cipher.encrypt(data)
                        client_sock.sendall(encrypted)
                except (socket.timeout, ConnectionResetError):
                    continue

    except Exception as e:
        print(f"Server error: {e}")
    finally:
        if remote_sock:
            remote_sock.close()
        client_sock.close()
        print("Connection closed")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 8388))
    server.listen(5)
    print("Server started on port 8388")

    try:
        while True:
            client_sock, addr = server.accept()
            client_sock.settimeout(30)
            print(f"\nNew connection from {addr}")
            threading.Thread(target=handle_client, args=(client_sock,)).start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
