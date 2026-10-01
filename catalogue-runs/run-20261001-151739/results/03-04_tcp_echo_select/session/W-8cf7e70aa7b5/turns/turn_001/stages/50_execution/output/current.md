import socket
import select
import threading
import sys
import time

MAX_CONNECTIONS = 64

def start_echo_server(host='127.0.0.1', port=0):
    """Start the echo server in a background thread.
    Returns the listening socket and the thread object.
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen()
    server_sock.setblocking(False)
    thread = threading.Thread(target=_run_server, args=(server_sock,), daemon=True)
    thread.start()
    return server_sock, thread

def _run_server(listen_sock):
    inputs = [listen_sock]
    client_count = 0
    while True:
        readable, _, _ = select.select(inputs, [], [], 1.0)
        for s in readable:
            if s is listen_sock:
                try:
                    client_sock, _ = listen_sock.accept()
                    client_sock.setblocking(False)
                except BlockingIOError:
                    continue
                if client_count < MAX_CONNECTIONS:
                    inputs.append(client_sock)
                    client_count += 1
                else:
                    try:
                        client_sock.sendall(b"Connection limit exceeded.\n")
                    finally:
                        client_sock.close()
            else:
                try:
                    data = s.recv(4096)
                except ConnectionResetError:
                    data = b''
                if not data:
                    inputs.remove(s)
                    s.close()
                    client_count -= 1
                else:
                    s.sendall(data)

# ---------- Test harness ----------

def _client_task(host, port, message, results, idx):
    with socket.create_connection((host, port)) as sock:
        sock.sendall(message.encode())
        sock.shutdown(socket.SHUT_WR)
        received = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            received += chunk
        results[idx] = received.decode()

def test_echo_server():
    host = '127.0.0.1'
    server_sock, server_thread = start_echo_server(host)
    _, port = server_sock.getsockname()
    msgs = ["Hello from client 1\n", "Second client says hi\n", "Third message\n"]
    results = [None, None, None]
    threads = []
    for i, msg in enumerate(msgs):
        t = threading.Thread(target=_client_task, args=(host, port, msg, results, i))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    # Verify echoes
    assert results == msgs, f"Echo mismatch: {results} != {msgs}"
    # Cleanup
    server_sock.close()
    time.sleep(0.5)  # give server thread a moment to notice closure
    print("Test passed.")

if __name__ == "__main__":
    test_echo_server()
