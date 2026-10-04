```python
import socket, threading

def handle(conn):
    with conn:
        f = conn.makefile("rwb")
        for line in f:
            f.write(line); f.flush()

def serve(port):
    srv = socket.socket(); srv.bind(("127.0.0.1", port)); srv.listen(64)
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()
```
Each client gets its own thread, so many clients are served concurrently. The listen backlog of 64 limits connections. Test: three clients send lines and check the echoes.
