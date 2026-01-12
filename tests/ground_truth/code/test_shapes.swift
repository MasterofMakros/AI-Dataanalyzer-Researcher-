// Swift Test File 1: Structs and Classes
// Expected: Extract struct and class definitions

import Foundation

struct Point {
    var x: Double
    var y: Double
    
    func distance(to other: Point) -> Double {
        let dx = x - other.x
        let dy = y - other.y
        return sqrt(dx * dx + dy * dy)
    }
}

class Shape {
    var name: String
    
    init(name: String) {
        self.name = name
    }
    
    func area() -> Double {
        fatalError("Muss Ã¼berschrieben werden")
    }
}

class Circle: Shape {
    var radius: Double
    
    init(radius: Double) {
        self.radius = radius
        super.init(name: "Kreis")
    }
    
    override func area() -> Double {
        return Double.pi * radius * radius
    }
}

let circle = Circle(radius: 5)
print("\(circle.name) FlÃ¤che: \(circle.area())")
