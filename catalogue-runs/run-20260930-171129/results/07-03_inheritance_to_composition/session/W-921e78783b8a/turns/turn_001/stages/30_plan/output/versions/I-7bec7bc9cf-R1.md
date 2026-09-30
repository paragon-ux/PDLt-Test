REFRACTOR the existing Python inheritance hierarchy to use composition
CREATE Protocol or ABC interfaces for FlyingBehavior, SwimmingBehavior, and DivingBehavior exposing fly, swim, and dive methods
IMPLEMENT concrete component classes that provide the original method implementations for each behavior
DEFINE new animal classes (e.g., Duck) that compose the appropriate behavior components instead of inheriting from multiple bases
ENSURE the composed objects expose fly, swim, and dive with identical signatures and output as the original classes
WRITE unit tests that instantiate both the original inheritance‑based classes and the new composition‑based classes
VERIFY that calling fly, swim, and dive on each comparable entity yields identical results
INCLUDE tests covering Animal, FlyingAnimal, SwimmingAnimal, FlyingSwimmingAnimal, DivingBird, and the behavior interfaces
