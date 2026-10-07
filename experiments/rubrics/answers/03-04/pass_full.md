```python
import select, socket

MAX_CLIENTS = 64

def serve(port=0, ready=None, stop=None):
    lsock = socket.socket()
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.bind(("127.0.0.1", port)); lsock.listen(128); lsock.setblocking(False)
    if ready: ready(lsock.getsockname()[1])
    clients: dict[socket.socket, bytearray] = {}
    try:
        while stop is None or not stop.is_set():
            readable, _, _ = select.select([lsock, *clients], [], [], 0.1)
            for s in readable:
                if s is lsock:
                    conn, _ = lsock.accept()
                    if len(clients) >= MAX_CLIENTS:
                        conn.sendall(b"server full\n"); conn.close(); continue
                    conn.setblocking(False); clients[conn] = bytearray()
                    continue
                try:
                    data = s.recv(4096)
                except ConnectionError:
                    data = b""
                if not data:
                    clients.pop(s, None); s.close(); continue
                buf = clients[s]; buf += data
                while b"\n" in buf:
                    line, _, rest = bytes(buf).partition(b"\n")
                    s.sendall(line + b"\n"); buf[:] = rest
    finally:
        for s in clients: s.close()
        lsock.close()
    return clients

# test: run the server in a thread (the test may), 3 concurrent clients
import threading, time
def test_echo():
    port, stop = [], threading.Event()
    state = {}
    t = threading.Thread(target=lambda: state.setdefault("left", serve(0, port.append, stop)), daemon=True)
    t.start()
    while not port: time.sleep(0.01)
    socks = [socket.create_connection(("127.0.0.1", port[0])) for _ in range(3)]
    for i, s in enumerate(socks): s.sendall(f"hello {i}\npart".encode())
    for i, s in enumerate(socks): s.sendall(b"ial\n")
    for i, s in enumerate(socks):
        got = b""
        while got.count(b"\n") < 2: got += s.recv(100)
        assert got == f"hello {i}\npartial\n".encode()
    for s in socks: s.close()
    time.sleep(0.3); stop.set(); t.join(2)
    assert state["left"] == {}      # every client removed
```
