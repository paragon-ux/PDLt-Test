# echo_server.py
import sys
import socket
import select
import argparse

MAX_CONNECTIONS = 64
REJECTION_MESSAGE = b"Maximum connections reached, try later.\n"

def main():
    parser = argparse.ArgumentParser(description="TCP echo server using select")
    parser.add_argument("port", type=int, help="Port to listen on (positive integer)")
    args = parser.parse_args()
    if args.port <= 0 or args.port > 65535:
        sys.exit("Port must be a positive integer between 1 and 65535")

    # Create listening socket
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind(("0.0.0.0", args.port))
    listen_sock.listen()
    listen_sock.setblocking(False)

    inputs = [listen_sock]
    client_sockets = {}

    while True:
        readable, _, _ = select.select(inputs, [], [])
        for s in readable:
            if s is listen_sock:
                # New connection
                client_sock, addr = listen_sock.accept()
                if len(client_sockets) >= MAX_CONNECTIONS:
                    client_sock.sendall(REJECTION_MESSAGE)
                    client_sock.close()
                else:
                    client_sock.setblocking(False)
                    inputs.append(client_sock)
                    client_sockets[client_sock] = addr
            else:
                data = s.recv(4096)
                if not data:
                    # Client closed connection
                    inputs.remove(s)
                    del client_sockets[s]
                    s.close()
                else:
                    s.sendall(data)

if __name__ == "__main__":
    main()

# test_echo_server.py
import subprocess
import socket
import threading
import time
import sys
import os

SERVER_SCRIPT = "echo_server.py"
HOST = "127.0.0.1"
PORT = 0  # let OS pick a free port

def run_server(port):
    # Run the server as a subprocess
    proc = subprocess.Popen([sys.executable, SERVER_SCRIPT, str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def client_thread(port, message, result_holder, idx):
    with socket.create_connection((HOST, port)) as sock:
        sock.sendall(message.encode())
        received = b""
        while len(received) < len(message.encode()):
            chunk = sock.recv(4096)
            if not chunk:
                break
            received += chunk
        result_holder[idx] = received.decode()

def main_test():
    # Choose a free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tmp:
        tmp.bind((HOST, 0))
        free_port = tmp.getsockname()[1]

    server_proc = run_server(free_port)
    # Give server a moment to start
    time.sleep(0.5)

    messages = ["Hello from client 1\nSecond line\n", "Client2 says hi\n", "Third client message\nLine2\nLine3\n"]
    results = [None, None, None]
    threads = []
    for i, msg in enumerate(messages):
        t = threading.Thread(target=client_thread, args=(free_port, msg, results, i))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    # Verify echoes
    assert results == messages, f"Echo mismatch: {results} vs {messages}"

    # Shutdown server by terminating process
    server_proc.terminate()
    server_proc.wait(timeout=5)
    print("Test passed")

if __name__ == "__main__":
    main_test()
