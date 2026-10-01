PARSE the supplied Python inheritance hierarchy definitions.
EXTRACT the behavior methods associated with flying and swimming.
DEFINE Protocol interfaces for flying behavior and for swimming behavior.
REFRACTOR the Animal class to serve as a simple base class without behavior implementations.
IMPLEMENT concrete behavior components that provide flying capabilities and swimming capabilities.
REFRACTOR DivingBird to compose the appropriate behavior components instead of inheriting from FlyingAnimal or SwimmingAnimal.
REFRACTOR Duck to compose both flying and swimming behavior components without requiring a FlyingSwimmingAnimal base class.
ELIMINATE multiple inheritance from all class definitions.
INCLUDE verbatim the entities Animal, FlyingAnimal, SwimmingAnimal, FlyingSwimmingAnimal, DivingBird, Duck, Protocol in the refactored code.
WRITE unit tests that instantiate both the original hierarchy classes and the refactored composition-based classes, invoke their behavior methods, and assert equivalent outcomes.
EXECUTE the unit tests to verify behavioral parity between the original and refactored implementations.
PACKAGE the refactored code and unit tests as the final deliverable.
