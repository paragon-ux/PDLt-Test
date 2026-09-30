import frostbitedb

# Connect to FrostbiteDB instance (default localhost)
client = frostbitedb.Client()

# Create (or get) collection named "example_collection"
collection = client.get_collection('example_collection')

# Insert three documents into the collection
docs = [
    {'id': 1, 'name': 'Alice', 'age': 30},
    {'id': 2, 'name': 'Bob', 'age': 25},
    {'id': 3, 'name': 'Charlie', 'age': 35},
]
collection.insert_many(docs)

# Query the collection to retrieve the inserted documents
retrieved = list(collection.find({}))
print(retrieved)
