<?php
// PHP Test File 1: Classes
// Expected: Extract class definitions

namespace App\Services;

class UserService {
    private \ = [];
    
    public function addUser(string \, string \): void {
        \->users[] = [
            'name' => \,
            'email' => \,
            'created_at' => date('Y-m-d H:i:s')
        ];
    }
    
    public function findByEmail(string \): ?array {
        foreach (\->users as \) {
            if (\['email'] === \) {
                return \;
            }
        }
        return null;
    }
    
    public function count(): int {
        return count(\->users);
    }
}

\ = new UserService();
\->addUser('Max', 'max@example.com');
echo "Users: " . \->count();
