# echo_server.py
import socket
import select
import threading
import time

MAX_CONNECTIONS = 64
REJECTION_MESSAGE = b"Server at capacity, connection rejected.\n"

def run_server(host='127.0.0.1', port=0):
    """Start a TCP echo server using select.
    Returns the listening socket and the thread running the server.
    """
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((host, port))
    listen_sock.listen()
    listen_sock.setblocking(False)
    server = _Server(listen_sock)
    thread = threading.Thread(target=server.serve, daemon=True)
    thread.start()
    return listen_sock.getsockname(), thread, server

class _Server:
    def __init__(self, listen_sock: socket.socket):
        self.listen_sock = listen_sock
        self.inputs = [listen_sock]
        self.client_addrs = {}
        self.running = True

    def serve(self):
        while self.running:
            readable, _, _ = select.select(self.inputs, [], [], 0.5)
            for sock in readable:
                if sock is self.listen_sock:
                    self._accept_new()
                else:
                    self._handle_client(sock)
        self._cleanup()

    def _accept_new(self):
        try:
            client_sock, addr = self.listen_sock.accept()
            client_sock.setblocking(False)
            if len(self.inputs) - 1 < MAX_CONNECTIONS:
                self.inputs.append(client_sock)
                self.client_addrs[client_sock] = addr
            else:
                client_sock.sendall(REJECTION_MESSAGE)
                client_sock.close()
        except BlockingIOError:
            pass

    def _handle_client(self, client_sock: socket.socket):
        try:
            data = client_sock.recv(4096)
            if data:
                client_sock.sendall(data)  # echo preserving newlines
            else:
                # client closed connection
                self._remove_client(client_sock)
        except ConnectionResetError:
            self._remove_client(client_sock)
        except BlockingIOError:
            pass

    def _remove_client(self, client_sock: socket.socket):
        if client_sock in self.inputs:
            self.inputs.remove(client_sock)
        client_sock.close()
        self.client_addrs.pop(client_sock, None)

    def stop(self):
        self.running = False

    def _cleanup(self):
        for sock in self.inputs:
            sock.close()
        self.inputs.clear()
        self.client_addrs.clear()

# ---------- Test ----------
def _client_task(host, port, messages, results, idx):
    with socket.create_connection((host, port)) as sock:
        echoed = []
        for msg in messages:
            sock.sendall(msg.encode())
            # read exactly the same length back
            recv = b""
            while len(recv) < len(msg):
                part = sock.recv(4096)
                if not part:
                    break
                recv += part
            echoed.append(recv.decode())
        results[idx] = echoed

def test_echo_server():
    (host, port), server_thread, server = run_server(port=0)
    time.sleep(0.1)  # give server time to start
    client_msgs = [
        ["Hello from client 1\n", "Second line\n"],
        ["Client2 says hi\n"],
        ["Third client message\n", "Another line\n", "Last line\n"]
    ]
    results = [None, None, None]
    threads = []
    for i, msgs in enumerate(client_msgs):
        t = threading.Thread(target=_client_task, args=(host, port, msgs, results, i))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    # verify echoes
    for i, msgs in enumerate(client_msgs):
        assert results[i] == msgs, f"Echo mismatch for client {i}: {results[i]} != {msgs}"
    # stop server and ensure cleanup
    server.stop()
    server_thread.join()
    print("All tests passed.")

if __name__ == "__main__":
    test_echo_server()
