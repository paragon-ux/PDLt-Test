import socket
import select
import sys
import argparse

def run_server(host: str, port: int, max_clients: int = 64):
    # Create listening socket
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((host, port))
    listen_sock.listen()
    listen_sock.setblocking(False)

    inputs = [listen_sock]
    client_sockets = {}
    connection_count = 0

    print(f"Server listening on {host}:{port}")
    while True:
        readable, _, _ = select.select(inputs, [], [])
        for s in readable:
            if s is listen_sock:
                # New connection attempt
                client_sock, addr = listen_sock.accept()
                client_sock.setblocking(False)
                if connection_count < max_clients:
                    inputs.append(client_sock)
                    client_sockets[client_sock] = addr
                    connection_count += 1
                else:
                    # Reject excess connection
                    msg = "Maximum connections reached. Connection rejected.\n"
                    try:
                        client_sock.sendall(msg.encode())
                    finally:
                        client_sock.close()
                continue

            # Existing client socket has data
            try:
                data = s.recv(4096)
            except ConnectionResetError:
                data = b''
            if not data:
                # Client closed connection
                inputs.remove(s)
                s.close()
                client_sockets.pop(s, None)
                connection_count -= 1
                continue
            # Echo the received data back, preserving newline characters
            s.sendall(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TCP echo server using select.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=12345, help="Port to listen on (default: 12345)")
    args = parser.parse_args()
    run_server(args.host, args.port)
