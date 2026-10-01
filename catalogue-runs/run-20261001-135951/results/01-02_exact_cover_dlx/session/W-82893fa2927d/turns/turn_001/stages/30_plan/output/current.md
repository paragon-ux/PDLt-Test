IMPLEMENT Algorithm X with dancing links for exact cover problems
DEFINE the universe U = {1,2,3,4,5,6,7,8,9}
DEFINE the collection of sets S1 through S9
BUILD the dancing‑links data structure representing the matrix of element‑set incidences
EXECUTE the recursive search algorithm to generate all exact covers of U
FOR each generated solution
    VERIFY that the solution includes each element of U exactly once
    RECORD the solution if verification succeeds
EMIT the list of recorded exact‑cover solutions
DEVELOP a self‑contained test that invokes the implementation, checks that each emitted solution satisfies the verification criteria, and reports success or failure
