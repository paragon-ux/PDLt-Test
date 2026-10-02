```python
from __future__ import annotations
from typing import Protocol

# ---------- Protocol definitions ----------
class FlyingBehavior(Protocol):
    def fly(self) -> str: ...

class SwimmingBehavior(Protocol):
    def swim(self) -> str: ...

# ---------- Concrete behavior components ----------
class SimpleFlying:
    def __init__(self, name: str, wingspan: float):
        self._name = name
        self._wingspan = wingspan

    def fly(self) -> str:
        return f"{self._name} flies with {self._wingspan}m wingspan"

class SimpleSwimming:
    def __init__(self, name: str, max_depth: float):
        self._name = name
        self._max_depth = max_depth

    def swim(self) -> str:
        return f"{self._name} swims to {self._max_depth}m"

# ---------- Base animal class ----------
class Animal:
    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight

# ---------- Original inheritance hierarchy (kept for parity tests) ----------
class FlyingAnimal(Animal):
    def __init__(self, name: str, weight: float, wingspan: float):
        super().__init__(name, weight)
        self.wingspan = wingspan

    def fly(self) -> str:
        return f"{self.name} flies with {self.wingspan}m wingspan"

class SwimmingAnimal(Animal):
    def __init__(self, name: str, weight: float, max_depth: float):
        super().__init__(name, weight)
        self.max_depth = max_depth

    def swim(self) -> str:
        return f"{self.name} swims to {self.max_depth}m"

class FlyingSwimmingAnimal(FlyingAnimal, SwimmingAnimal):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float):
        FlyingAnimal.__init__(self, name, weight, wingspan)
        SwimmingAnimal.__init__(self, name, weight, max_depth)

class DivingBird(FlyingSwimmingAnimal):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float, dive_speed: float):
        super().__init__(name, weight, wingspan, max_depth)
        self.dive_speed = dive_speed

    def dive(self) -> str:
        return f"{self.name} dives at {self.dive_speed}m/s"

# ---------- Composition based classes ----------
class FlyingAnimalComp(Animal):
    def __init__(self, name: str, weight: float, wingspan: float):
        super().__init__(name, weight)
        self._fly_behavior = SimpleFlying(name, wingspan)

    def fly(self) -> str:
        return self._fly_behavior.fly()

class SwimmingAnimalComp(Animal):
    def __init__(self, name: str, weight: float, max_depth: float):
        super().__init__(name, weight)
        self._swim_behavior = SimpleSwimming(name, max_depth)

    def swim(self) -> str:
        return self._swim_behavior.swim()

class Duck(Animal, FlyingBehavior, SwimmingBehavior):
    def __init__(self, name: str, weight: float, wingspan: float, max_depth: float):
        super().__init__(name, weight)
        self._fly = SimpleFlying(name, wingspan)
        self._swim = SimpleSwimming(name, max_depth)

    def fly(self) -> str:
        return self._fly.fly()

    def swim(self) -> str:
        return self._swim.swim()

# ---------- Unit tests ----------
import unittest

class TestBehaviorParity(unittest.TestCase):
    def test_flying_animal(self):
        orig = FlyingAnimal("Eagle", 5.0, 2.5)
        comp = FlyingAnimalComp("Eagle", 5.0, 2.5)
        self.assertEqual(orig.fly(), comp.fly())

    def test_swimming_animal(self):
        orig = SwimmingAnimal("Fish", 1.0, 30.0)
        comp = SwimmingAnimalComp("Fish", 1.0, 30.0)
        self.assertEqual(orig.swim(), comp.swim())

    def test_flying_swimming_animal(self):
        orig = FlyingSwimmingAnimal("Penguin", 10.0, 1.2, 20.0)
        # Compose equivalent using Duck (behaviour only, no dive)
        duck = Duck("Penguin", 10.0, 1.2, 20.0)
        self.assertEqual(orig.fly(), duck.fly())
        self.assertEqual(orig.swim(), duck.swim())

    def test_diving_bird(self):
        orig = DivingBird("Cormorant", 3.0, 1.0, 15.0, 4.5)
        self.assertEqual(orig.dive(), "Cormorant dives at 4.5m/s")
        # Composition version does not have dive, ensure base behaviours match
        duck = Duck("Cormorant", 3.0, 1.0, 15.0)
        self.assertEqual(orig.fly(), duck.fly())
        self.assertEqual(orig.swim(), duck.swim())

if __name__ == "__main__":
    unittest.main()
```
