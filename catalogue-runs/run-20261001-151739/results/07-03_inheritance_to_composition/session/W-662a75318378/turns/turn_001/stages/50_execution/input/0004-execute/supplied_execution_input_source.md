The following code uses a deep inheritance hierarchy. Refactor it to use composition with explicit interfaces (Protocol classes or ABCs).

`python
class Animal:
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight

class FlyingAnimal(Animal):
    def __init__(self, name, weight, wingspan):
        super().__init__(name, weight)
        self.wingspan = wingspan
    def fly(self):
        return f"{self.name} flies with {self.wingspan}m wingspan"

class SwimmingAnimal(Animal):
    def __init__(self, name, weight, max_depth):
        super().__init__(name, weight)
        self.max_depth = max_depth
    def swim(self):
        return f"{self.name} swims to {self.max_depth}m"

class FlyingSwimmingAnimal(FlyingAnimal, SwimmingAnimal):
    def __init__(self, name, weight, wingspan, max_depth):
        FlyingAnimal.__init__(self, name, weight, wingspan)
        SwimmingAnimal.__init__(self, name, weight, max_depth)

class DivingBird(FlyingSwimmingAnimal):
    def __init__(self, name, weight, wingspan, max_depth, dive_speed):
        super().__init__(name, weight, wingspan, max_depth)
        self.dive_speed = dive_speed
    def dive(self):
        return f"{self.name} dives at {self.dive_speed}m/s"
`

The composition version should avoid multiple inheritance entirely. A Duck should be composable from Flying + Swimming without requiring a FlyingSwimmingAnimal base class. Include tests proving behavioral parity.
