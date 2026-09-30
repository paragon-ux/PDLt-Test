IDENTIFY the input sequence and its length
VERIFY that the key domain permits a linear‑time comparison‑based sort (e.g., bounded integer range or fixed‑size digit representation)
SELECT a stable, in‑place, O(1)‑extra‑space linear‑time sorting strategy appropriate to the verified key domain (such as an in‑place radix sort with constant‑space digit counting)
FOR each digit position from least‑significant to most‑significant
STABLY partition the sequence based on the current digit using only constant extra storage
ENDFOR
OUTPUT the now‑sorted sequence
