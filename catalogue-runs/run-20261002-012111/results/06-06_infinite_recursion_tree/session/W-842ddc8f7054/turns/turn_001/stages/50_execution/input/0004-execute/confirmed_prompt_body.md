DIAGNOSE why the serialize function causes a stack overflow on deep trees
IDENTIFY the recursion depth limitation in the serialize implementation
REWRITE the serialize function as an iterative version that can handle tree depth >= 100000 without recursion
PROVIDE the iterative serialization code
BUILD test code that constructs a chain of 50000 nodes
USE the iterative serializer to serialize the constructed chain
VERIFY the serialization completes without stack overflow
NOTE the identifier i in the code if present
