// Go Test File 1: Structs and Functions
// Expected: Extract struct and function definitions

package main

import (
    "fmt"
    "time"
)

type Order struct {
    ID        int
    Customer  string
    Total     float64
    CreatedAt time.Time
}

func NewOrder(customer string, total float64) *Order {
    return &Order{
        ID:        generateID(),
        Customer:  customer,
        Total:     total,
        CreatedAt: time.Now(),
    }
}

func (o *Order) String() string {
    return fmt.Sprintf("Order #%d: %s - %.2f EUR", o.ID, o.Customer, o.Total)
}

func generateID() int {
    return int(time.Now().UnixNano() % 10000)
}

func main() {
    order := NewOrder("Max Mustermann", 149.99)
    fmt.Println(order)
}
