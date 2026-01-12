// Java Test File 1: Classes
// Expected: Extract class and method definitions

package com.example.test;

import java.util.ArrayList;
import java.util.List;

public class CustomerService {
    private List<Customer> customers;
    
    public CustomerService() {
        this.customers = new ArrayList<>();
    }
    
    public void addCustomer(Customer customer) {
        customers.add(customer);
    }
    
    public Customer findById(int id) {
        return customers.stream()
            .filter(c -> c.getId() == id)
            .findFirst()
            .orElse(null);
    }
    
    public static void main(String[] args) {
        CustomerService service = new CustomerService();
        System.out.println("Service gestartet");
    }
}
