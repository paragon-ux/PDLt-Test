TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Refactor the provided deep inheritance hierarchy of Python classes (Animal, FlyingAnimal, SwimmingAnimal, FlyingSwimmingAnimal, DivingBird) to use composition with explicit interfaces (Protocol classes or ABCs) instead of multiple inheritance. Create composable components for flying and swimming behaviors that can be combined, e.g., a Duck composed from Flying and Swimming components without a FlyingSwimmingAnimal base class. Preserve the existing methods (fly, swim, dive) and their output formats. Include tests that verify the new composition version behaves identically to the original inheritance version.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Animal
- FlyingAnimal
- SwimmingAnimal
- FlyingSwimmingAnimal
- DivingBird
- fly
- swim
- dive
- composition
- Protocol
- ABC
