# Python Test File 2: Classes
# Expected: Extract class definitions and methods

class Person:
    """ReprÃ¤sentiert eine Person."""
    
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    
    def introduce(self) -> str:
        return f"Ich bin {self.name}, {self.age} Jahre alt."

class Employee(Person):
    """Ein Mitarbeiter ist eine Person mit Gehalt."""
    
    def __init__(self, name: str, age: int, salary: float):
        super().__init__(name, age)
        self.salary = salary
