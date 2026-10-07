Your FizzBuzz loop runs once for each of the 100 numbers, and each iteration does at most two modulo checks (`i % 3`, `i % 5`) and one print, all constant time. So it is **O(n)** time for n numbers, with **O(1)** extra memory.

It can't be asymptotically faster: it must emit n lines, so any implementation is Ω(n). Only constant factors can improve: compute `i % 15` once or use counters instead of modulo, collect the lines and print them with one `"\n".join(...)` instead of 100 prints, or cycle through the fixed 15-element pattern. For n = 100 none of this is measurable.
