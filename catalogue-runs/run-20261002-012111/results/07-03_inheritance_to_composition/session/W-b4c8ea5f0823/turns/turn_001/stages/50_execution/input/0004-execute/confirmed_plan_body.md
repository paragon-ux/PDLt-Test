REFRACTOR the supplied Python class hierarchy into a composition-based design using Protocols and abstract base classes
ELIMINATE multiple inheritance by replacing inheritance with component composition
DEFINE a FlyingBehavior protocol with a fly method signature
DEFINE a SwimmingBehavior protocol with a swim method signature
IMPLEMENT concrete components for FlyingBehavior and SwimmingBehavior that produce the original formatted string outputs
REFRACTOR each original animal class to contain references to the appropriate behavior components rather than inheriting from multiple bases
PRESERVE the original method behavior for fly, swim, and dive by delegating to the components or retaining the method bodies, ensuring identical formatted string outputs
COMPOSE a Duck class by injecting FlyingBehavior and SwimmingBehavior components without requiring a FlyingSwimmingAnimal base class
DEVELOP unit tests that instantiate both the original inheritance-based classes and the new composition-based classes, invoke their behaviors, and assert that outputs match
VERIFY behavioral parity across all test cases
