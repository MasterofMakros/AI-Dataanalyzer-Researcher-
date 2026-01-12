// JavaScript Test File 2: Classes
// Expected: Extract class definitions

class ShoppingCart {
    constructor() {
        this.items = [];
    }
    
    addItem(product, quantity) {
        this.items.push({ product, quantity });
    }
    
    getTotal() {
        return this.items.reduce((sum, item) => 
            sum + item.product.price * item.quantity, 0);
    }
}

export default ShoppingCart;
