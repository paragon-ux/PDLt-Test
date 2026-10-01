import socket
import select
import sys
import threading
import time

MAX_CONNECTIONS = 64
REJECT_MESSAGE = b"Too many connections, try again later.\n"

def start_echo_server(host: str, port: int):
    """Start a TCP echo server using only the select module.

    The server listens on the given host and port, accepts up to
    ``MAX_CONNECTIONS`` concurrent clients, and echoes each line
    (including the newline) back to the originating client.
    """
    # Create listening socket
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((host, port))
    listen_sock.listen()
    listen_sock.setblocking(False)

    # Lists for select
    inputs = [listen_sock]
    client_buffers = {}
    client_addresses = {}

    while True:
        readable, _, exceptional = select.select(inputs, [], inputs)
        for s in readable:
            if s is listen_sock:
                # New connection attempt
                client_sock, addr = listen_sock.accept()
                client_sock.setblocking(False)
                if len(client_buffers) >= MAX_CONNECTIONS:
                    # Reject excess connection
                    try:
                        client_sock.sendall(REJECT_MESSAGE)
                    finally:
                        client_sock.close()
                    continue
                inputs.append(client_sock)
                client_buffers[client_sock] = b""
                client_addresses[client_sock] = addr
            else:
                data = s.recv(4096)
                if data:
                    client_buffers[s] += data
                    # Process complete lines
                    while b"\n" in client_buffers[s]:
                        line, rest = client_buffers[s].split(b"\n", 1)
                        line += b"\n"
                        s.sendall(line)
                        client_buffers[s] = rest
                else:
                    # No data means client closed connection
                    inputs.remove(s)
                    s.close()
                    del client_buffers[s]
                    del client_addresses[s]
        for s in exceptional:
            inputs.remove(s)
            s.close()
            client_buffers.pop(s, None)
            client_addresses.pop(s, None)

# ---------- Test Suite ----------

def _run_server_in_thread(port):
    server_thread = threading.Thread(target=start_echo_server, args=("127.0.0.1", port), daemon=True)
    server_thread.start()
    # Give server a moment to start
    time.sleep(0.2)
    return server_thread

def _client_interaction(port, messages, results):
    with socket.create_connection(("127.0.0.1", port)) as sock:
        for msg in messages:
            sock.sendall(msg.encode())
            # Receive echo line by line
            echoed = b""
            while not echoed.endswith(b"\n"):
                chunk = sock.recv(4096)
                if not chunk:
                    break
                echoed += chunk
            results.append(echoed.decode())
        # Close will trigger graceful removal on server side

def test_echo_server():
    test_port = 0  # let OS pick an available port
    # Create a temporary listening socket to discover a free port
    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_sock.bind(("127.0.0.1", 0))
    _, free_port = temp_sock.getsockname()
    temp_sock.close()

    _run_server_in_thread(free_port)

    # Prepare client messages
    client1_msgs = ["Hello from client 1\n", "Second line 1\n"]
    client2_msgs = ["Client 2 says hi\n"]
    client3_msgs = ["Third client message\n", "Another line\n", "Last line\n"]

    results = []
    threads = []
    for msgs in (client1_msgs, client2_msgs, client3_msgs):
        t = threading.Thread(target=_client_interaction, args=(free_port, msgs, results))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    # Verify echoed messages match sent messages preserving newline
    expected = client1_msgs + client2_msgs + client3_msgs
    assert results == expected, f"Echo mismatch: expected {expected!r}, got {results!r}"
    print("All echo tests passed.")

if __name__ == "__main__":
    # Run test when executed directly
    test_echo_server()
