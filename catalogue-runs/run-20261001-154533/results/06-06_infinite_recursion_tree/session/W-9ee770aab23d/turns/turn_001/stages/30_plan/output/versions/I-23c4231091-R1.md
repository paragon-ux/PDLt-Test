ANALYZE the existing recursive serialize method to identify the recursion depth that triggers stack overflow.
DESIGN an iterative alternative that uses an explicit stack to traverse the node tree and supports depths of at least 100,000.
WRITE the iterative serialize function in Python.
CONSTRUCT a linear chain of 50,000 Node objects forming a depth‑50000 tree.
EXECUTE the iterative serialize function on the constructed chain.
VERIFY that the serialization completes without raising a stack overflow.
OUTPUT the Python code for the iterative serialize function and the verification test script.
