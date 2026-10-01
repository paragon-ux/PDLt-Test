TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Refactor the provided Python code that defines a deep inheritance hierarchy of animal classes (Animal, FlyingAnimal, SwimmingAnimal, FlyingSwimmingAnimal, DivingBird) to use composition instead of multiple inheritance. Introduce explicit interfaces using Protocol classes or abstract base classes. Create composable components so that a Duck can be built from Flying and Swimming capabilities without requiring a FlyingSwimmingAnimal base class. Preserve the original behavior (fly, swim, dive) and provide tests that demonstrate behavioral parity with the original implementation.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Animal
- FlyingAnimal
- SwimmingAnimal
- FlyingSwimmingAnimal
- DivingBird
- Duck
- fly
- swim
- dive
- composition
- Protocol
- tests
