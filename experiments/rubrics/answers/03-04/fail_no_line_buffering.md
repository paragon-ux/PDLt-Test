```python
import select, socket

def serve(port):
    srv = socket.socket(); srv.bind(("127.0.0.1", port)); srv.listen()
    inputs = [srv]
    while True:
        r, _, _ = select.select(inputs, [], [])
        for s in r:
            if s is srv:
                c, _ = srv.accept(); inputs.append(c)
            else:
                data = s.recv(1024)
                if data:
                    s.sendall(data)
                else:
                    inputs.remove(s); s.close()
```
Test: start the server in a thread, connect three clients, send "a\n", "b\n", "c\n" and check each gets its message back.
