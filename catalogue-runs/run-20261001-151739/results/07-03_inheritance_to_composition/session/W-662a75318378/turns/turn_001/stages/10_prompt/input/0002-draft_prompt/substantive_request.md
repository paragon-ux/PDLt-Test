TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Refactor the provided Python inheritance hierarchy (class Animal, FlyingAnimal, SwimmingAnimal, FlyingSwimmingAnimal, DivingBird) to a composition-based design using explicit interfaces (Protocol classes or abstract base classes). Eliminate multiple inheritance, ensuring that a Duck can be composed from Flying and Swimming behaviors without requiring a FlyingSwimmingAnimal base class. Provide unit tests that demonstrate behavioral parity with the original implementation.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Animal
- FlyingAnimal
- SwimmingAnimal
- FlyingSwimmingAnimal
- DivingBird
- Duck
- Protocol
