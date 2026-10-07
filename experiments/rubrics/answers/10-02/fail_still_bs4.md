```python
import requests
from bs4 import BeautifulSoup

def extract_links(url):
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    return [a["href"] for a in soup.find_all("a", href=True)]
```
Uses the html.parser backend as requested.
