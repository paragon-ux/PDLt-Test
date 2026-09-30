REFRACTOR the provided deep inheritance hierarchy of Python classes (Animal, FlyingAnimal, SwimmingAnimal, FlyingSwimmingAnimal, DivingBird) to use COMPOSITION with explicit interfaces (Protocol classes or ABCs) instead of multiple inheritance.
CREATE composable components for flying and swimming behaviors that expose the methods fly, swim, and dive.
DEFINE Protocol or ABC interfaces for each behavior (e.g., FlyingBehavior, SwimmingBehavior, DivingBehavior).
IMPLEMENT concrete components that provide the original method implementations and output formats.
COMPOSE new class definitions (e.g., Duck) by combining the appropriate behavior components rather than inheriting from a FlyingSwimmingAnimal base class.
ENSURE that all original methods (fly, swim, dive) remain available on the composed objects with identical signatures and output.
PROVIDE unit tests that instantiate both the original inheritance‑based classes and the new composition‑based classes and VERIFY that calling fly, swim, and dive yields identical results for each comparable entity.
INCLUDE tests for each of the operative task entities: Animal, FlyingAnimal, SwimmingAnimal, FlyingSwimmingAnimal, DivingBird, fly, swim, dive, composition, Protocol, ABC.
