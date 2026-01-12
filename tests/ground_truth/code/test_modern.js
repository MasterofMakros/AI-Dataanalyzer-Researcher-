// JavaScript Test File 3: Modern ES6+
// Expected: Extract modern syntax

import { createApp } from 'vue';

const config = {
    apiUrl: 'https://api.example.com',
    timeout: 5000,
    retries: 3
};

const [first, ...rest] = [1, 2, 3, 4, 5];
const merged = { ...config, debug: true };

const users = ['Anna', 'Ben', 'Clara'];
const upperUsers = users.map(u => u.toUpperCase());

console.log(upperUsers);
