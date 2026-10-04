FIRST(E)=FIRST(T)=FIRST(F)={(,id}, FIRST(E')={+,ε}, FIRST(T')={*,ε}.
FOLLOW(E)=FOLLOW(E')={),$}, FOLLOW(T)=FOLLOW(T')={+,),$}, FOLLOW(F)={+,*,),$}.
The table follows directly from these sets, and the grammar is LL(1) since no cell has two entries. Parsing id + id * id succeeds.
