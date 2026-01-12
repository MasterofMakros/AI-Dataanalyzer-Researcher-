// TypeScript Test File 1: Interfaces
// Expected: Extract interface definitions

interface User {
    id: number;
    name: string;
    email: string;
    createdAt: Date;
}

interface Product {
    id: string;
    title: string;
    price: number;
    inStock: boolean;
}

function createUser(name: string, email: string): User {
    return {
        id: Math.random(),
        name,
        email,
        createdAt: new Date()
    };
}

export { User, Product, createUser };
