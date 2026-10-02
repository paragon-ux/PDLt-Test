import itertools, json

def search():
    domain = [1,2,3]
    nodes = 0
    for x,y,z in itertools.product(domain, repeat=3):
        nodes += 1
        if not (x != y and y != z and z != x):
            continue
        if x + y + z != 4:
            continue
        if not (x >= y and y >= z):
            continue
        # found solution
        return True, nodes, {'x':x,'y':y,'z':z}
    return False, nodes, None

found, nodes, sol = search()
if found:
    witness = {
        "polarity": "positive",
        "data": sol
    }
else:
    witness = {
        "polarity": "negative",
        "basis": "search",
        "search_exhausted": True,
        "nodes_explored": nodes,
        "method": "exhaustive enumeration",
        "argument": None,
        "domain": None,
        "provisional": False
    }
print('WITNESS: ' + json.dumps(witness))

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "negative",
    "basis": "search",
    "search_exhausted": true,
    "nodes_explored": 27,
    "method": "exhaustive enumeration",
    "argument": null,
    "domain": null,
    "provisional": false
  }
}
```
