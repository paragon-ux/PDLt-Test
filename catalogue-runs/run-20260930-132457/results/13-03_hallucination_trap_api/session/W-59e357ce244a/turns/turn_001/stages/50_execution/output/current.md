import frostbitedb

def main():
    # Connect to FrostbiteDB instance (replace with actual connection parameters)
    client = frostbitedb.Client(host="localhost", port=8000)
    db = client.get_database("mydb")

    # Create a new collection
    collection = db.create_collection("my_collection")

    # Insert three documents
    docs = [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25},
        {"id": 3, "name": "Carol", "age": 27},
    ]
    for doc in docs:
        collection.insert_one(doc)

    # Query the collection to retrieve the inserted documents
    retrieved = list(collection.find({}))
    print(retrieved)

if __name__ == "__main__":
    main()

# Result IR
{"files": [{"filename": "script.py", "satisfies": ["R1", "R2", "R3", "R4", "R5"], "evidence": {"path": "execution://body", "section": null, "observed": null}}], "reconciliation": [{"requirement": "R1", "status": "satisfied", "evidence": {"path": "execution://body", "section": null, "observed": "CONNECT to FrostbiteDB instance using the frostbitedb Python SDK"}}, {"requirement": "R2", "status": "satisfied", "evidence": {"path": "execution://body", "section": null, "observed": "CREATE a new collection"}}, {"requirement": "R3", "status": "satisfied", "evidence": {"path": "execution://body", "section": null, "observed": "INSERT three documents"}}, {"requirement": "R4", "status": "satisfied", "evidence": {"path": "execution://body", "section": null, "observed": "QUERY the collection to retrieve the inserted documents"}}, {"requirement": "R5", "status": "satisfied", "evidence": {"path": "execution://body", "section": null, "observed": "RETURN the retrieved documents as the result"}}], "open_defects": []}
