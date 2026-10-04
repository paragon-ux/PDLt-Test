```python
#!/usr/bin/env python3
import argparse, json, sys, urllib.request

BASE = "https://jsonplaceholder.typicode.com"

def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        text = resp.read().decode()
        return json.loads(text) if text else {}

def main(argv=None):
    p = argparse.ArgumentParser(prog="posts")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    c = sub.add_parser("create"); c.add_argument("--title", required=True); c.add_argument("--body", required=True)
    c.add_argument("--user-id", type=int, default=1)
    d = sub.add_parser("delete"); d.add_argument("id", type=int)
    args = p.parse_args(argv)
    try:
        if args.cmd == "list":
            result = call("GET", "/posts")
        elif args.cmd == "create":
            result = call("POST", "/posts", {"title": args.title, "body": args.body, "userId": args.user_id})
        else:
            result = call("DELETE", f"/posts/{args.id}")
    except urllib.error.HTTPError as e:
        print(f"error: HTTP {e.code}", file=sys.stderr); return 1
    print(json.dumps(result, indent=2)); return 0

if __name__ == "__main__":
    sys.exit(main())
```
