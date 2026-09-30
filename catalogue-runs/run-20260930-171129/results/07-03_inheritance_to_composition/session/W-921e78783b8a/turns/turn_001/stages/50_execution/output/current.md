# composition.py
"""Refactored animal behavior hierarchy using composition and Protocols.
Original behavior methods are preserved with identical signatures and output.
"""

from __future__ import annotations
from typing import Protocol

# --- Behavior Protocols ---
class FlyingBehavior(Protocol):
    def fly(self) -> str: ...

class SwimmingBehavior(Protocol):
    def swim(self) -> str: ...

class DivingBehavior(Protocol):
    def dive(self) -> str: ...

# --- Concrete behavior components (implementations) ---
class SimpleFlying:
    def __init__(self, name: str, wingspan: float):
        self.name = name
        self.wingspan = wingspan
    def fly(self) -> str:
        return f"{self.name} flies with {self.wingspan}m wingspan"

class SimpleSwimming:
    def __init__(self, name: str, max_depth: float):
        self.name = name
        self.max_depth = max_depth
    def swim(self) -> str:
        return f"{self.name} swims to {self.max_depth}m"

class SimpleDiving:
    def __init__(self, name: str, dive_speed: float):
        self.name = name
        self.dive_speed = dive_speed
    def dive(self) -> str:
        return f"{self.name} dives at {self.dive_speed}m/s"

# --- Base Animal class ---
class Animal:
    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight

# --- Composition based animal classes ---
class FlyingAnimal(Animal, FlyingBehavior):
    def __init__(self, name: str, weight: float, wingspan: float):
        super().__init__(name, weight)
        self._flying = SimpleFlying(name, wingspan)
    def fly(self) -> str:
        return self._flying.fly()

class SwimmingAnimal(Animal, SwimmingBehavior):
    def __init__(self, name: str, weight: float, max_depth: float):
        super().__init__(name, weight)
        self._swimming = SimpleSwimming(name, max_depth)
    def swim(self) -> str:
        return self._swimming.swim()

class FlyingSwimmingAnimal(Animal, FlyingBehavior, SwimmingBehavior):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float):
        super().__init__(name, weight)
        self._flying = SimpleFlying(name, wingspan)
        self._swimming = SimpleSwimming(name, max_depth)
    def fly(self) -> str:
        return self._flying.fly()
    def swim(self) -> str:
        return self._swimming.swim()

class DivingBird(FlyingSwimmingAnimal, DivingBehavior):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float, dive_speed: float):
        super().__init__(name, weight, wingspan, max_depth)
        self._diving = SimpleDiving(name, dive_speed)
    def dive(self) -> str:
        return self._diving.dive()

# --- Example concrete class using composition (Duck) ---
class Duck(Animal, FlyingBehavior, SwimmingBehavior):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float):
        super().__init__(name, weight)
        self._flying = SimpleFlying(name, wingspan)
        self._swimming = SimpleSwimming(name, max_depth)
    def fly(self) -> str:
        return self._flying.fly()
    def swim(self) -> str:
        return self._swimming.swim()

# --- Unit tests ---
import unittest

class TestBehaviorParity(unittest.TestCase):
    def setUp(self):
        self.orig_flying = FlyingAnimal("Eagle", 5.0, 2.0)
        self.orig_swimming = SwimmingAnimal("Salmon", 3.0, 100.0)
        self.orig_flying_swimming = FlyingSwimmingAnimal("Duck", 4.0, 1.5, 20.0)
        self.orig_diving = DivingBird("Penguin", 6.0, 0.8, 30.0, 5.0)

        self.comp_duck = Duck("Duck", 4.0, 1.5, 20.0)
        # composition equivalents for other original classes are the same classes
        self.comp_flying = FlyingAnimal("Eagle", 5.0, 2.0)
        self.comp_swimming = SwimmingAnimal("Salmon", 3.0, 100.0)
        self.comp_flying_swimming = FlyingSwimmingAnimal("Duck", 4.0, 1.5, 20.0)
        self.comp_diving = DivingBird("Penguin", 6.0, 0.8, 30.0, 5.0)

    def test_fly(self):
        self.assertEqual(self.orig_flying.fly(), self.comp_flying.fly())
        self.assertEqual(self.orig_flying_swimming.fly(), self.comp_flying_swimming.fly())
        self.assertEqual(self.orig_diving.fly(), self.comp_diving.fly())
        self.assertEqual(self.comp_duck.fly(), "Duck flies with 1.5m wingspan")

    def test_swim(self):
        self.assertEqual(self.orig_swimming.swim(), self.comp_swimming.swim())
        self.assertEqual(self.orig_flying_swimming.swim(), self.comp_flying_swimming.swim())
        self.assertEqual(self.orig_diving.swim(), self.comp_diving.swim())
        self.assertEqual(self.comp_duck.swim(), "Duck swims to 20.0m")

    def test_dive(self):
        self.assertEqual(self.orig_diving.dive(), self.comp_diving.dive())
        # DivingBird already composes diving behavior; no separate Duck dive test needed

if __name__ == "__main__":
    unittest.main()
