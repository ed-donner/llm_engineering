"""Test module for TypeScript language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_typescript_detection():
    """Test the TypeScript language detection functionality."""
    detector = LanguageDetector()
    
    # Sample TypeScript code
    typescript_code = """
import { Component, OnInit } from '@angular/core';
import axios from 'axios';

// Interface definition
interface User {
    id: number;
    name: string;
    email: string;
    isActive: boolean;
}

// Type alias
type UserResponse = User[] | null;

// Enum
enum UserRole {
    Admin = 'ADMIN',
    User = 'USER',
    Guest = 'GUEST'
}

// Class with type annotations
export class UserService {
    private apiUrl: string;
    private users: User[] = [];
    
    constructor(baseUrl: string) {
        this.apiUrl = `${baseUrl}/users`;
    }
    
    // Async method with return type
    public async getUsers(): Promise<User[]> {
        try {
            const response = await axios.get<UserResponse>(this.apiUrl);
            if (response.data) {
                this.users = response.data;
                return this.users;
            }
            return [];
        } catch (error) {
            console.error('Error fetching users:', error);
            return [];
        }
    }
    
    // Method with typed parameters
    public getUserById(id: number): User | undefined {
        return this.users.find(user => user.id === id);
    }
    
    // Method with union type parameters
    public filterUsers(status: boolean | null): User[] {
        if (status === null) return this.users;
        return this.users.filter(user => user.isActive === status);
    }
}

// Generic class
class DataStore<T> {
    private items: T[] = [];
    
    public add(item: T): void {
        this.items.push(item);
    }
    
    public getAll(): T[] {
        return this.items;
    }
}

// Decorator example
@Component({
    selector: 'app-user-list',
    template: '<div>User List Component</div>'
})
class UserListComponent implements OnInit {
    users: User[] = [];
    userService: UserService;
    
    constructor() {
        this.userService = new UserService('https://api.example.com');
    }
    
    async ngOnInit(): Promise<void> {
        this.users = await this.userService.getUsers();
        console.log('Users loaded:', this.users.length);
    }
}

// Function with default parameters
function createUser(name: string, email: string, isActive: boolean = true): User {
    const id = Math.floor(Math.random() * 1000);
    return { id, name, email, isActive };
}

// Main code
const userStore = new DataStore<User>();
const newUser = createUser('John Doe', 'john@example.com');
userStore.add(newUser);

console.log('Users in store:', userStore.getAll().length);
"""
    
    # Test the detection
    assert detector.detect_typescript(typescript_code) == True
    assert detector.detect_language(typescript_code) == "TypeScript"
    
    # Check that it's distinguishable from JavaScript
    js_code = """
function greet(name) {
    console.log(`Hello, ${name}!`);
}

const user = {
    name: 'John',
    age: 30
};

greet(user.name);
"""
    assert detector.detect_typescript(js_code) == False
    assert detector.detect_language(js_code) == "JavaScript"
    
    # Check validation
    valid, _ = detector.validate_language(typescript_code, "TypeScript")
    assert valid == True


if __name__ == "__main__":
    test_typescript_detection()
    print("All TypeScript detection tests passed!")
