import os
import json

# Placeholder connection details – adjust as needed
HOST = os.getenv("FROSTBITE_HOST", "localhost")
PORT = int(os.getenv("FROSTBITE_PORT", "8080"))
USERNAME = os.getenv("FROSTBITE_USER", "admin")
PASSWORD = os.getenv("FROSTBITE_PASS", "password")

# Import the FrostbiteDB SDK (assumed to be installed in the environment)
try:
    import frostbitedb
except ImportError as e:
    raise RuntimeError("FrostbiteDB SDK not available in this environment")

# Connect to the FrostbiteDB instance
client = frostbitedb.Client(host=HOST, port=PORT, username=USERNAME, password=PASSWORD)

# Create a new collection
collection_name = "my_collection"
client.create_collection(collection_name)
collection = client.get_collection(collection_name)

# Insert three documents
documents = [
    {"_id": 1, "name": "Alice", "age": 30},
    {"_id": 2, "name": "Bob", "age": 25},
    {"_id": 3, "name": "Charlie", "age": 35},
]
collection.insert_many(documents)

# Query the collection to retrieve the inserted documents
retrieved = list(collection.find({}))
print(json.dumps(retrieved, indent=2))
