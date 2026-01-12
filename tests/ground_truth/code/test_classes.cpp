// C++ Test File 1: Classes
// Expected: Extract class definitions

#include <iostream>
#include <string>
#include <vector>

class Vehicle {
protected:
    std::string brand;
    int year;

public:
    Vehicle(const std::string& b, int y) : brand(b), year(y) {}
    
    virtual void display() const {
        std::cout << "Brand: " << brand << ", Year: " << year << std::endl;
    }
    
    virtual ~Vehicle() = default;
};

class Car : public Vehicle {
private:
    int doors;

public:
    Car(const std::string& b, int y, int d) 
        : Vehicle(b, y), doors(d) {}
    
    void display() const override {
        Vehicle::display();
        std::cout << "Doors: " << doors << std::endl;
    }
};

int main() {
    Car myCar("BMW", 2024, 4);
    myCar.display();
    return 0;
}
