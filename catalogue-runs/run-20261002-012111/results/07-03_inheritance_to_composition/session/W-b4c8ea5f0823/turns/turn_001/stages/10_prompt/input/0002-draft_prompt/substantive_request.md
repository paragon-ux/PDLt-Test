TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Refactor the supplied Python class hierarchy (class Animal, FlyingAnimal, SwimmingAnimal, FlyingSwimmingAnimal, DivingBird) into a composition-based design using explicit interfaces such as Protocol classes or abstract base classes. The new design must eliminate multiple inheritance, create separate Flying and Swimming components, and allow a Duck to be composed from these components without requiring a FlyingSwimmingAnimal base class. Preserve the original method behavior (fly, swim, dive) with identical formatted string outputs. Provide unit tests that demonstrate behavioral parity between the original inheritance version and the composition version.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Animal
- FlyingAnimal
- SwimmingAnimal
- FlyingSwimmingAnimal
- DivingBird
- Duck
- Protocol
- fly
- swim
- dive
- m
