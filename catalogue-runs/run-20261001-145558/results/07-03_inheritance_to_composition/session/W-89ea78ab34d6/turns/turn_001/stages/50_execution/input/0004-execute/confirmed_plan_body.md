ANALYZE the existing Python code defining Animal, FlyingAnimal, SwimmingAnimal, FlyingSwimmingAnimal, DivingBird, and Duck with their fly, swim, and dive methods
IDENTIFY the multiple inheritance relationships to be eliminated
DEFINE Protocol interfaces for FlyingCapability, SwimmingCapability, and DivingCapability using typing.Protocol or abc.ABC
IMPLEMENT composable component classes FlyingComponent, SwimmingComponent, and DivingComponent that provide fly, swim, and dive behavior respectively
REFACTOR each existing class to accept the appropriate component(s) via composition and delegate behavior to those components
REBUILD Duck by composing FlyingComponent and SwimmingComponent without inheriting from FlyingSwimmingAnimal
ENSURE DivingBird composes DivingComponent (and other needed components) preserving its dive behavior
UPDATE any remaining class hierarchies to rely on composition and Protocols rather than multiple inheritance
WRITE unit tests that instantiate the original class hierarchy and the new composition-based hierarchy, invoke fly, swim, and dive where applicable, and assert behavioral parity
