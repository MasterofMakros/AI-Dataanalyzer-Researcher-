# Python Test File 1: Functions
# Expected: Extract function names and docstrings

def calculate_sum(a: int, b: int) -> int:
    """Berechnet die Summe zweier Zahlen."""
    return a + b

def greet(name: str) -> str:
    """BegrÃ¼ÃŸt eine Person mit Namen."""
    return f"Hallo, {name}!"

if __name__ == "__main__":
    result = calculate_sum(5, 10)
    print(greet("Welt"))
