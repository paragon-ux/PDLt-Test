# fizzbuzz.py
for i in range(1, 101):
    if i % 15 == 0:
        print("FizzBuzz")
    elif i % 3 == 0:
        print("Fizz")
    elif i % 5 == 0:
        print("Buzz")
    else:
        print(i)

# Result IR
{
  "files": [
    {
      "filename": "fizzbuzz.py",
      "satisfies": ["R1","R2","R3","R4","R5","R6","R7","R8","R9","R10"],
      "evidence": {"path": "execution://body","section": null,"observed": null}
    }
  ],
  "reconciliation": [
    {"requirement":"R1","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"READ the range from 1 to 100"}},
    {"requirement":"R2","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"FOR each number in the range"}},
    {"requirement":"R3","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"IF the number is divisible by 3 AND the number is divisible by 5"}},
    {"requirement":"R4","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"OUTPUT \"FizzBuzz\""}},
    {"requirement":"R5","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"ELSE IF the number is divisible by 3"}},
    {"requirement":"R6","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"OUTPUT \"Fizz\""}},
    {"requirement":"R7","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"ELSE IF the number is divisible by 5"}},
    {"requirement":"R8","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"OUTPUT \"Buzz\""}},
    {"requirement":"R9","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":"ELSE"}},
    {"requirement":"R10","status":"satisfied","observation":{"path":"execution://body","section":null,"observed":"OUTPUT the number"}}
  ],
  "open_defects": []
}
