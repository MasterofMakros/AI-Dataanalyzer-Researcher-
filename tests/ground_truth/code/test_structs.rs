// Rust Test File 1: Structs and Implementations
// Expected: Extract struct definitions and impl blocks

use std::fmt;

#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    fn new(width: u32, height: u32) -> Self {
        Rectangle { width, height }
    }
    
    fn area(&self) -> u32 {
        self.width * self.height
    }
    
    fn perimeter(&self) -> u32 {
        2 * (self.width + self.height)
    }
}

impl fmt::Display for Rectangle {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Rectangle {}x{}", self.width, self.height)
    }
}

fn main() {
    let rect = Rectangle::new(30, 50);
    println!("{} hat FlÃ¤che {} qm", rect, rect.area());
}
