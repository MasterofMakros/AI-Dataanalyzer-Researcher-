/* C Test File 1: Functions
 * Expected: Extract function signatures
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_SIZE 100

typedef struct {
    int id;
    char name[50];
    float price;
} Product;

Product* create_product(int id, const char* name, float price) {
    Product* p = (Product*)malloc(sizeof(Product));
    p->id = id;
    strncpy(p->name, name, 49);
    p->price = price;
    return p;
}

void print_product(const Product* p) {
    printf("ID: %d, Name: %s, Preis: %.2f EUR\n", 
           p->id, p->name, p->price);
}

int main() {
    Product* laptop = create_product(1, "Laptop", 999.99);
    print_product(laptop);
    free(laptop);
    return 0;
}
