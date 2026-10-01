import abc
from typing import Protocol

# Original classes for reference (not used in composition version)
class Animal:
    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight

# Protocol interfaces (explicit capabilities)
class FlyingCapability(Protocol):
    def fly(self) -> str: ...

class SwimmingCapability(Protocol):
    def swim(self) -> str: ...

class DivingCapability(Protocol):
    def dive(self) -> str: ...

# Component classes providing concrete behavior
class FlyingComponent:
    def __init__(self, name: str, wingspan: float):
        self.name = name
        self.wingspan = wingspan

    def fly(self) -> str:
        return f"{self.name} flies with {self.wingspan}m wingspan"

class SwimmingComponent:
    def __init__(self, name: str, max_depth: float):
        self.name = name
        self.max_depth = max_depth

    def swim(self) -> str:
        return f"{self.name} swims to {self.max_depth}m"

class DivingComponent:
    def __init__(self, name: str, dive_speed: float):
        self.name = name
        self.dive_speed = dive_speed

    def dive(self) -> str:
        return f"{self.name} dives at {self.dive_speed}m/s"

# Refactored animal classes using composition
class ComposedAnimal:
    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight

class Duck(ComposedAnimal, FlyingCapability, SwimmingCapability):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float):
        super().__init__(name, weight)
        self.flying = FlyingComponent(name, wingspan)
        self.swimming = SwimmingComponent(name, max_depth)

    def fly(self) -> str:
        return self.flying.fly()

    def swim(self) -> str:
        return self.swimming.swim()

class DivingBird(ComposedAnimal, FlyingCapability, SwimmingCapability, DivingCapability):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float, dive_speed: float):
        super().__init__(name, weight)
        self.flying = FlyingComponent(name, wingspan)
        self.swimming = SwimmingComponent(name, max_depth)
        self.diving = DivingComponent(name, dive_speed)

    def fly(self) -> str:
        return self.flying.fly()

    def swim(self) -> str:
        return self.swimming.swim()

    def dive(self) -> str:
        return self.diving.dive()

# Unit tests demonstrating parity with original hierarchy
import unittest

class TestCompositionParity(unittest.TestCase):
    def setUp(self):
        # Original hierarchy instances (kept for parity check)
        class OrigAnimal:
            def __init__(self, name, weight):
                self.name = name
                self.weight = weight
        class OrigFlyingAnimal(OrigAnimal):
            def __init__(self, name, weight, wingspan):
                super().__init__(name, weight)
                self.wingspan = wingspan
            def fly(self):
                return f"{self.name} flies with {self.wingspan}m wingspan"
        class OrigSwimmingAnimal(OrigAnimal):
            def __init__(self, name, weight, max_depth):
                super().__init__(name, weight)
                self.max_depth = max_depth
            def swim(self):
                return f"{self.name} swims to {self.max_depth}m"
        class OrigFlyingSwimmingAnimal(OrigFlyingAnimal, OrigSwimmingAnimal):
            def __init__(self, name, weight, wingspan, max_depth):
                OrigFlyingAnimal.__init__(self, name, weight, wingspan)
                OrigSwimmingAnimal.__init__(self, name, weight, max_depth)
        class OrigDivingBird(OrigFlyingSwimmingAnimal):
            def __init__(self, name, weight, wingspan, max_depth, dive_speed):
                super().__init__(name, weight, wingspan, max_depth)
                self.dive_speed = dive_speed
            def dive(self):
                return f"{self.name} dives at {self.dive_speed}m/s"
        class OrigDuck(OrigFlyingSwimmingAnimal):
            pass
        self.OrigDuck = OrigDuck
        self.OrigDivingBird = OrigDivingBird

    def test_duck_behavior(self):
        duck_orig = self.OrigDuck('Daffy', 5.0, 0.8, 2.0)
        duck_new = Duck('Daffy', 5.0, 0.8, 2.0)
        self.assertEqual(duck_orig.fly(), duck_new.fly())
        self.assertEqual(duck_orig.swim(), duck_new.swim())

    def test_diving_bird_behavior(self):
        bird_orig = self.OrigDivingBird('Penguin', 15.0, 1.2, 30.0, 3.5)
        bird_new = DivingBird('Penguin', 15.0, 1.2, 30.0, 3.5)
        self.assertEqual(bird_orig.fly(), bird_new.fly())
        self.assertEqual(bird_orig.swim(), bird_new.swim())
        self.assertEqual(bird_orig.dive(), bird_new.dive())

if __name__ == '__main__':
    unittest.main()
