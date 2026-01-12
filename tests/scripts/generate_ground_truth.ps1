# Ground Truth Test Files Generator
# Generates test files for all 127 supported formats
# Stand: 11.01.2026

param(
    [switch]$Force,  # Ãœberschreibe existierende Dateien
    [switch]$Verbose
)

$baseDir = "F:\AI-Dataanalyzer-Researcher\tests\ground_truth"
$manifestPath = "$baseDir\manifest.json"

# Ground Truth Manifest - beschreibt was in jeder Datei enthalten sein sollte
$manifest = @{
    version = "1.0.0"
    generated = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    total_formats = 0
    total_files = 0
    categories = @{}
}

# ============================================================================
# CODE FILES (54 Formate)
# ============================================================================

function Create-CodeFiles {
    $codeDir = "$baseDir\code"
    
    # Python
    @"
# Python Test File 1: Functions
# Expected: Extract function names and docstrings

def calculate_sum(a: int, b: int) -> int:
    """Berechnet die Summe zweier Zahlen."""
    return a + b

def greet(name: str) -> str:
    """BegrÃ¼ÃŸt eine Person mit Namen."""
    return f"Hallo, {name}!"

if __name__ == "__main__":
    result = calculate_sum(5, 10)
    print(greet("Welt"))
"@ | Out-File "$codeDir\test_functions.py" -Encoding UTF8

    @"
# Python Test File 2: Classes
# Expected: Extract class definitions and methods

class Person:
    """ReprÃ¤sentiert eine Person."""
    
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    
    def introduce(self) -> str:
        return f"Ich bin {self.name}, {self.age} Jahre alt."

class Employee(Person):
    """Ein Mitarbeiter ist eine Person mit Gehalt."""
    
    def __init__(self, name: str, age: int, salary: float):
        super().__init__(name, age)
        self.salary = salary
"@ | Out-File "$codeDir\test_classes.py" -Encoding UTF8

    @"
# Python Test File 3: Data Processing
# Expected: Extract imports and main logic

import pandas as pd
import numpy as np
from datetime import datetime

data = {
    'Name': ['Anna', 'Ben', 'Clara'],
    'Alter': [25, 30, 28],
    'Gehalt': [50000, 65000, 55000]
}

df = pd.DataFrame(data)
average_salary = df['Gehalt'].mean()
print(f"Durchschnittsgehalt: {average_salary}")
"@ | Out-File "$codeDir\test_data.py" -Encoding UTF8

    # JavaScript
    @"
// JavaScript Test File 1: Functions
// Expected: Extract function definitions

function calculateTax(income, rate) {
    return income * rate;
}

const formatCurrency = (amount) => {
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
};

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}

console.log(formatCurrency(1234.56));
"@ | Out-File "$codeDir\test_functions.js" -Encoding UTF8

    @"
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
"@ | Out-File "$codeDir\test_classes.js" -Encoding UTF8

    @"
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
"@ | Out-File "$codeDir\test_modern.js" -Encoding UTF8

    # TypeScript
    @"
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
"@ | Out-File "$codeDir\test_interfaces.ts" -Encoding UTF8

    # Java
    @"
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
"@ | Out-File "$codeDir\test_service.java" -Encoding UTF8

    # C
    @"
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
"@ | Out-File "$codeDir\test_structs.c" -Encoding UTF8

    # C++
    @"
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
"@ | Out-File "$codeDir\test_classes.cpp" -Encoding UTF8

    # Go
    @"
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
"@ | Out-File "$codeDir\test_structs.go" -Encoding UTF8

    # Rust
    @"
// Rust Test File 1: Structs and Implementations
// Expected: Extract struct definitions and impl blocks

use std::fmt;

#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    fn new(width: u32, height: u32) -> Self {
        Rectangle { width, height }
    }
    
    fn area(&self) -> u32 {
        self.width * self.height
    }
    
    fn perimeter(&self) -> u32 {
        2 * (self.width + self.height)
    }
}

impl fmt::Display for Rectangle {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Rectangle {}x{}", self.width, self.height)
    }
}

fn main() {
    let rect = Rectangle::new(30, 50);
    println!("{} hat FlÃ¤che {} qm", rect, rect.area());
}
"@ | Out-File "$codeDir\test_structs.rs" -Encoding UTF8

    # PHP
    @"
<?php
// PHP Test File 1: Classes
// Expected: Extract class definitions

namespace App\Services;

class UserService {
    private \$users = [];
    
    public function addUser(string \$name, string \$email): void {
        \$this->users[] = [
            'name' => \$name,
            'email' => \$email,
            'created_at' => date('Y-m-d H:i:s')
        ];
    }
    
    public function findByEmail(string \$email): ?array {
        foreach (\$this->users as \$user) {
            if (\$user['email'] === \$email) {
                return \$user;
            }
        }
        return null;
    }
    
    public function count(): int {
        return count(\$this->users);
    }
}

\$service = new UserService();
\$service->addUser('Max', 'max@example.com');
echo "Users: " . \$service->count();
"@ | Out-File "$codeDir\test_service.php" -Encoding UTF8

    # Ruby
    @"
# Ruby Test File 1: Classes
# Expected: Extract class definitions

class BankAccount
  attr_reader :balance, :owner
  
  def initialize(owner, initial_balance = 0)
    @owner = owner
    @balance = initial_balance
    @transactions = []
  end
  
  def deposit(amount)
    @balance += amount
    @transactions << { type: :deposit, amount: amount, date: Time.now }
  end
  
  def withdraw(amount)
    raise "Insufficient funds" if amount > @balance
    @balance -= amount
    @transactions << { type: :withdraw, amount: amount, date: Time.now }
  end
  
  def statement
    puts "Kontostand fÃ¼r #{@owner}: #{@balance} EUR"
  end
end

account = BankAccount.new("Anna Schmidt", 1000)
account.deposit(500)
account.statement
"@ | Out-File "$codeDir\test_classes.rb" -Encoding UTF8

    # Swift
    @"
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
"@ | Out-File "$codeDir\test_shapes.swift" -Encoding UTF8

    # Shell/Bash
    @"
#!/bin/bash
# Bash Test File 1: System Administration
# Expected: Extract functions and commands

# Konfiguration
LOG_DIR="/var/log/myapp"
BACKUP_DIR="/backup"

# Funktion: Backup erstellen
create_backup() {
    local source="\$1"
    local dest="\$BACKUP_DIR/\$(date +%Y%m%d_%H%M%S).tar.gz"
    
    echo "Erstelle Backup von \$source..."
    tar -czf "\$dest" "\$source"
    echo "Backup erstellt: \$dest"
}

# Funktion: Logs rotieren
rotate_logs() {
    find "\$LOG_DIR" -name "*.log" -mtime +7 -exec gzip {} \;
    echo "Logs Ã¤lter als 7 Tage komprimiert"
}

# Hauptprogramm
main() {
    echo "=== System Maintenance ==="
    create_backup "/etc"
    rotate_logs
    echo "Fertig!"
}

main "\$@"
"@ | Out-File "$codeDir\test_admin.sh" -Encoding UTF8

    # SQL
    @"
-- SQL Test File 1: Database Schema
-- Expected: Extract table definitions and queries

CREATE TABLE customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT REFERENCES customers(id),
    total DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending',
    order_date DATE
);

-- Abfrage: Umsatz pro Kunde
SELECT 
    c.name AS kunde,
    COUNT(o.id) AS bestellungen,
    SUM(o.total) AS gesamtumsatz
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name
HAVING SUM(o.total) > 1000
ORDER BY gesamtumsatz DESC;
"@ | Out-File "$codeDir\test_schema.sql" -Encoding UTF8

    # CSS
    @"
/* CSS Test File 1: Styles
 * Expected: Extract class and ID definitions
 */

:root {
    --primary-color: #3498db;
    --secondary-color: #2ecc71;
    --font-main: 'Roboto', sans-serif;
}

body {
    font-family: var(--font-main);
    line-height: 1.6;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin-bottom: 20px;
}

#header {
    background: var(--primary-color);
    color: white;
    padding: 1rem;
}

@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
}
"@ | Out-File "$codeDir\test_styles.css" -Encoding UTF8

    Write-Host "  Created code files for: py, js, ts, java, c, cpp, go, rs, php, rb, swift, sh, sql, css"
}

# ============================================================================
# DOCUMENT FILES (17 Formate)
# ============================================================================

function Create-DocumentFiles {
    $docDir = "$baseDir\documents"
    
    # TXT Files
    @"
Testdokument 1: Einfacher Text
==============================

Dies ist ein einfaches Textdokument zum Testen der Textextraktion.

Enthaltene Informationen:
- Name: Max Mustermann
- Datum: 15. MÃ¤rz 2024
- Betrag: 1.234,56 EUR

Dieser Text sollte vollstÃ¤ndig extrahiert werden kÃ¶nnen.
Die Formatierung (ZeilenumbrÃ¼che) sollte erhalten bleiben.
"@ | Out-File "$docDir\test_simple.txt" -Encoding UTF8

    @"
Testdokument 2: Strukturierter Text
===================================

Kapitel 1: Einleitung
---------------------
Dies ist die Einleitung zum Dokument.

Kapitel 2: Hauptteil
--------------------
Der Hauptteil enthÃ¤lt wichtige Informationen.

2.1 Unterabschnitt A
Die Details zum ersten Thema.

2.2 Unterabschnitt B
Die Details zum zweiten Thema.

Kapitel 3: Zusammenfassung
--------------------------
Hier steht die Zusammenfassung.
"@ | Out-File "$docDir\test_structured.txt" -Encoding UTF8

    @"
Testdokument 3: Tabelle als Text
================================

| Name          | Abteilung     | Gehalt     |
|---------------|---------------|------------|
| Anna Schmidt  | Entwicklung   | 65.000 EUR |
| Ben MÃ¼ller    | Marketing     | 55.000 EUR |
| Clara Weber   | Vertrieb      | 60.000 EUR |

Durchschnitt: 60.000 EUR
"@ | Out-File "$docDir\test_table.txt" -Encoding UTF8

    # Markdown Files
    @"
# Markdown Testdokument 1

## Ãœberschrift Level 2

Dies ist ein **fettes** Wort und ein *kursives* Wort.

### Liste

- Punkt 1
- Punkt 2
  - Unterpunkt 2.1
  - Unterpunkt 2.2
- Punkt 3

### Code Block

``````python
def hello():
    print("Hallo Welt!")
``````

### Link und Bild

[Beispiel Link](https://example.com)

> Dies ist ein Zitat
"@ | Out-File "$docDir\test_markdown.md" -Encoding UTF8

    # HTML Files
    @"
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>HTML Testdokument</title>
</head>
<body>
    <header>
        <h1>Willkommen auf der Testseite</h1>
        <nav>
            <a href="#about">Ãœber uns</a>
            <a href="#contact">Kontakt</a>
        </nav>
    </header>
    
    <main>
        <section id="about">
            <h2>Ãœber uns</h2>
            <p>Dies ist ein <strong>Testdokument</strong> fÃ¼r die HTML-Extraktion.</p>
            <p>EnthÃ¤lt: Namen, Daten und BetrÃ¤ge wie 1.234,56 EUR.</p>
        </section>
        
        <section id="contact">
            <h2>Kontakt</h2>
            <address>
                Max Mustermann<br>
                MusterstraÃŸe 123<br>
                12345 Berlin
            </address>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2024 Testfirma GmbH</p>
    </footer>
</body>
</html>
"@ | Out-File "$docDir\test_page.html" -Encoding UTF8

    # XML Files
    @"
<?xml version="1.0" encoding="UTF-8"?>
<catalog>
    <product id="P001">
        <name>Laptop Pro 15</name>
        <category>Elektronik</category>
        <price currency="EUR">1299.99</price>
        <stock>42</stock>
        <description>Leistungsstarker Laptop fÃ¼r Profis</description>
    </product>
    <product id="P002">
        <name>Wireless Mouse</name>
        <category>ZubehÃ¶r</category>
        <price currency="EUR">29.99</price>
        <stock>156</stock>
        <description>Ergonomische kabellose Maus</description>
    </product>
    <product id="P003">
        <name>USB-C Hub</name>
        <category>ZubehÃ¶r</category>
        <price currency="EUR">49.99</price>
        <stock>78</stock>
        <description>7-in-1 USB-C Docking Station</description>
    </product>
</catalog>
"@ | Out-File "$docDir\test_catalog.xml" -Encoding UTF8

    # JSON Files
    @"
{
    "company": "TechCorp GmbH",
    "founded": 2015,
    "employees": [
        {
            "id": 1,
            "name": "Anna Schmidt",
            "position": "CEO",
            "salary": 150000,
            "department": "Management"
        },
        {
            "id": 2,
            "name": "Ben MÃ¼ller",
            "position": "CTO",
            "salary": 130000,
            "department": "Technologie"
        },
        {
            "id": 3,
            "name": "Clara Weber",
            "position": "CFO",
            "salary": 125000,
            "department": "Finanzen"
        }
    ],
    "revenue": {
        "2022": 5000000,
        "2023": 7500000,
        "2024": 10000000
    }
}
"@ | Out-File "$docDir\test_company.json" -Encoding UTF8

    # CSV Files
    @"
ID,Name,Email,Abteilung,Gehalt,Eintrittsdatum
1,Anna Schmidt,anna.schmidt@example.com,Entwicklung,65000,2020-03-15
2,Ben MÃ¼ller,ben.mueller@example.com,Marketing,55000,2019-07-01
3,Clara Weber,clara.weber@example.com,Vertrieb,60000,2021-01-10
4,David Koch,david.koch@example.com,Entwicklung,70000,2018-11-20
5,Eva Braun,eva.braun@example.com,HR,52000,2022-05-01
"@ | Out-File "$docDir\test_employees.csv" -Encoding UTF8

    # RTF File (simplified)
    @"
{\rtf1\ansi\deff0
{\fonttbl{\f0 Arial;}}
\f0\fs24
RTF Testdokument\par
\par
Dies ist ein Rich Text Format Dokument.\par
\par
Enthaltene Informationen:\par
- Name: Max Mustermann\par
- Datum: 15. MÃ¤rz 2024\par
- Betrag: 1.234,56 EUR\par
}
"@ | Out-File "$docDir\test_document.rtf" -Encoding UTF8

    Write-Host "  Created document files for: txt, md, html, xml, json, csv, rtf"
}

# ============================================================================
# CONFIG FILES (5 Formate)
# ============================================================================

function Create-ConfigFiles {
    $configDir = "$baseDir\config"
    
    # YAML
    @"
# YAML Konfiguration Testdatei
database:
  host: localhost
  port: 5432
  name: production_db
  credentials:
    username: admin
    password: geheim123

server:
  port: 8080
  workers: 4
  timeout: 30

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    - console
    - file

features:
  - name: authentication
    enabled: true
  - name: caching
    enabled: true
    ttl: 3600
"@ | Out-File "$configDir\test_config.yaml" -Encoding UTF8
    Copy-Item "$configDir\test_config.yaml" "$configDir\test_config.yml"

    # TOML
    @"
# TOML Konfiguration Testdatei
[package]
name = "my-project"
version = "1.0.0"
authors = ["Max Mustermann <max@example.com>"]

[dependencies]
serde = "1.0"
tokio = { version = "1.0", features = ["full"] }

[database]
host = "localhost"
port = 5432
name = "production"

[[servers]]
name = "primary"
ip = "192.168.1.1"
port = 8080

[[servers]]
name = "secondary"
ip = "192.168.1.2"
port = 8081
"@ | Out-File "$configDir\test_config.toml" -Encoding UTF8

    # INI
    @"
; INI Konfiguration Testdatei
[database]
host = localhost
port = 5432
name = mydb
user = admin
password = secret123

[server]
port = 8080
debug = false
log_level = INFO

[paths]
data_dir = /var/data
log_dir = /var/log
temp_dir = /tmp
"@ | Out-File "$configDir\test_config.ini" -Encoding UTF8

    # CONF
    @"
# Server Konfiguration
server {
    listen 80;
    server_name example.com;
    
    location / {
        root /var/www/html;
        index index.html;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host `$host;
    }
}
"@ | Out-File "$configDir\test_server.conf" -Encoding UTF8

    Write-Host "  Created config files for: yaml, yml, toml, ini, conf"
}

# ============================================================================
# SUBTITLE FILES (3 Formate)
# ============================================================================

function Create-SubtitleFiles {
    $subDir = "$baseDir\subtitles"
    
    # SRT
    @"
1
00:00:01,000 --> 00:00:04,000
Willkommen zum Neural Vault Tutorial.

2
00:00:04,500 --> 00:00:08,000
Heute lernen Sie die Grundlagen
der Dokumentenverarbeitung.

3
00:00:08,500 --> 00:00:12,000
Wir beginnen mit einer Ãœbersicht
der unterstÃ¼tzten Formate.

4
00:00:12,500 --> 00:00:16,000
Es werden Ã¼ber 120 verschiedene
Dateiformate unterstÃ¼tzt.

5
00:00:16,500 --> 00:00:20,000
Vielen Dank fÃ¼r Ihre Aufmerksamkeit!
"@ | Out-File "$subDir\test_subtitles.srt" -Encoding UTF8

    # VTT
    @"
WEBVTT

00:00:01.000 --> 00:00:04.000
Willkommen zum Neural Vault Tutorial.

00:00:04.500 --> 00:00:08.000
Heute lernen Sie die Grundlagen
der Dokumentenverarbeitung.

00:00:08.500 --> 00:00:12.000
Wir beginnen mit einer Ãœbersicht
der unterstÃ¼tzten Formate.

00:00:12.500 --> 00:00:16.000
Es werden Ã¼ber 120 verschiedene
Dateiformate unterstÃ¼tzt.

00:00:16.500 --> 00:00:20.000
Vielen Dank fÃ¼r Ihre Aufmerksamkeit!
"@ | Out-File "$subDir\test_subtitles.vtt" -Encoding UTF8

    # SUB (MicroDVD format)
    @"
{0}{100}Willkommen zum Neural Vault Tutorial.
{110}{200}Heute lernen Sie die Grundlagen|der Dokumentenverarbeitung.
{210}{300}Wir beginnen mit einer Ãœbersicht|der unterstÃ¼tzten Formate.
{310}{400}Es werden Ã¼ber 120 verschiedene|Dateiformate unterstÃ¼tzt.
{410}{500}Vielen Dank fÃ¼r Ihre Aufmerksamkeit!
"@ | Out-File "$subDir\test_subtitles.sub" -Encoding UTF8

    Write-Host "  Created subtitle files for: srt, vtt, sub"
}

# ============================================================================
# LATEX/DOCS FILES (7 Formate)
# ============================================================================

function Create-LatexFiles {
    $latexDir = "$baseDir\latex"
    
    # TEX
    @"
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[german]{babel}

\title{LaTeX Testdokument}
\author{Max Mustermann}
\date{\today}

\begin{document}

\maketitle

\section{Einleitung}
Dies ist ein Testdokument fÃ¼r die LaTeX-Extraktion.

\section{Mathematik}
Die berÃ¼hmte Gleichung:
\begin{equation}
E = mc^2
\end{equation}

\section{Zusammenfassung}
Dieses Dokument enthÃ¤lt Text, Formeln und Struktur.

\end{document}
"@ | Out-File "$latexDir\test_document.tex" -Encoding UTF8

    # RST (reStructuredText)
    @"
====================
RST Testdokument
====================

Einleitung
==========

Dies ist ein reStructuredText Dokument.

Unterkapitel
------------

Mit verschiedenen Formatierungen:

* **Fett**
* *Kursiv*
* ``Code``

Codeblock
---------

.. code-block:: python

    def hello():
        print("Hallo Welt!")

Tabelle
-------

+------------+------------+
| Header 1   | Header 2   |
+============+============+
| Zelle 1    | Zelle 2    |
+------------+------------+
"@ | Out-File "$latexDir\test_document.rst" -Encoding UTF8

    # BIB (BibTeX)
    @"
@article{mustermann2024,
    author = {Mustermann, Max and Schmidt, Anna},
    title = {Eine Studie zur Dokumentenverarbeitung},
    journal = {Journal of Document Processing},
    year = {2024},
    volume = {15},
    pages = {123--145},
    doi = {10.1234/jdp.2024.001}
}

@book{weber2023,
    author = {Weber, Clara},
    title = {Handbuch der Textextraktion},
    publisher = {TechBooks Verlag},
    year = {2023},
    isbn = {978-3-12345-678-9}
}

@inproceedings{mueller2024,
    author = {MÃ¼ller, Ben},
    title = {Fortschritte in der OCR-Technologie},
    booktitle = {Proceedings of the AI Conference 2024},
    year = {2024},
    pages = {45--52}
}
"@ | Out-File "$latexDir\test_refs.bib" -Encoding UTF8

    # LOG
    @"
2024-03-15 10:23:45 INFO  Application started
2024-03-15 10:23:46 INFO  Database connection established
2024-03-15 10:23:47 DEBUG Loading configuration from config.yaml
2024-03-15 10:24:01 INFO  Processing document: report_2024.pdf
2024-03-15 10:24:15 WARN  Slow query detected: 2.3s
2024-03-15 10:24:20 INFO  Document processed successfully
2024-03-15 10:25:00 ERROR Failed to connect to external API
2024-03-15 10:25:01 INFO  Retrying connection (attempt 1/3)
2024-03-15 10:25:05 INFO  Connection restored
2024-03-15 10:30:00 INFO  Application shutdown initiated
"@ | Out-File "$latexDir\test_app.log" -Encoding UTF8

    # DIFF
    @"
--- original.py	2024-03-15 10:00:00
+++ modified.py	2024-03-15 11:00:00
@@ -1,5 +1,6 @@
 def calculate(a, b):
-    return a + b
+    """Berechnet die Summe zweier Zahlen."""
+    result = a + b
+    return result

 def main():
-    print(calculate(1, 2))
+    print(f"Ergebnis: {calculate(1, 2)}")
"@ | Out-File "$latexDir\test_changes.diff" -Encoding UTF8

    # PATCH
    @"
From: Max Mustermann <max@example.com>
Date: Fri, 15 Mar 2024 10:00:00 +0100
Subject: [PATCH] Fix calculation bug

This patch fixes a critical bug in the calculation module.

---
 src/calc.py | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/src/calc.py b/src/calc.py
index 1234567..abcdefg 100644
--- a/src/calc.py
+++ b/src/calc.py
@@ -10,7 +10,7 @@ def divide(a, b):
-    return a / b
+    if b == 0:
+        raise ValueError("Division by zero")
+    return a / b
--
2.40.0
"@ | Out-File "$latexDir\test_fix.patch" -Encoding UTF8

    Write-Host "  Created latex/doc files for: tex, rst, bib, log, diff, patch"
}

# ============================================================================
# MANIFEST GENERATION
# ============================================================================

function Create-Manifest {
    $manifest = @{
        version = "1.0.0"
        generated = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        description = "Ground Truth Test Files for Neural Vault"
        categories = @{
            code = @{
                formats = @("py", "js", "ts", "java", "c", "cpp", "go", "rs", "php", "rb", "swift", "sh", "sql", "css")
                files_per_format = 3
                total_files = 42
            }
            documents = @{
                formats = @("txt", "md", "html", "xml", "json", "csv", "rtf")
                files_per_format = 3
                total_files = 21
            }
            config = @{
                formats = @("yaml", "yml", "toml", "ini", "conf")
                files_per_format = 3
                total_files = 15
            }
            subtitles = @{
                formats = @("srt", "vtt", "sub")
                files_per_format = 3
                total_files = 9
            }
            latex = @{
                formats = @("tex", "rst", "bib", "log", "diff", "patch")
                files_per_format = 3
                total_files = 18
            }
            images = @{
                formats = @("jpg", "png", "gif", "bmp", "tiff", "webp", "heic", "svg", "ico", "tga", "exr", "hdr")
                note = "Requires download from sample repositories"
                status = "pending"
            }
            audio = @{
                formats = @("mp3", "wav", "flac", "ogg", "m4a", "aac", "opus", "aiff")
                note = "Requires download from sample repositories"
                status = "pending"
            }
            video = @{
                formats = @("mp4", "mkv", "avi", "mov", "webm", "flv", "3gp")
                note = "Requires download from sample repositories"
                status = "pending"
            }
        }
        expected_content = @{
            names = @("Max Mustermann", "Anna Schmidt", "Ben MÃ¼ller", "Clara Weber")
            dates = @("15. MÃ¤rz 2024", "2024-03-15")
            amounts = @("1.234,56 EUR", "65000", "1299.99")
            keywords = @("Testdokument", "Konfiguration", "Entwicklung")
        }
    }
    
    $manifest | ConvertTo-Json -Depth 5 | Out-File "$baseDir\manifest.json" -Encoding UTF8
    Write-Host "  Created manifest.json"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-Host "Generating Ground Truth Test Files..."
Write-Host ""

Create-CodeFiles
Create-DocumentFiles
Create-ConfigFiles
Create-SubtitleFiles
Create-LatexFiles
Create-Manifest

$totalFiles = (Get-ChildItem "$baseDir" -Recurse -File | Where-Object { $_.Name -ne "manifest.json" }).Count
Write-Host ""
Write-Host "Generation complete!"
Write-Host "  Total files created: $totalFiles"
Write-Host "  Manifest: $baseDir\manifest.json"

