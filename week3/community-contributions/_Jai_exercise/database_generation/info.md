# 🚀 Synthetic Database Generator

## Overview

Synthetic Database Generator is an AI-powered application that automatically creates realistic relational database schemas and synthetic datasets for various business domains such as E-Commerce, Healthcare, Banking, Hospital Management, Hotel Booking, Food Delivery, HR Management, and more.

The application leverages Large Language Models (LLMs) to design production-like database structures and generate high-quality sample data that can be used for:

- Application development
- Database prototyping
- Testing and QA
- Data engineering projects
- AI/ML model training
- Text-to-SQL dataset creation
- Educational purposes

---

## ✨ Features

### 📐 Intelligent Schema Generation

Generate realistic relational database schemas based on a selected application domain.

Features include:

- Multiple related tables
- Primary Keys
- Foreign Keys
- Realistic column names
- Business-specific relationships
- Structured JSON schema output

---

### 📊 Synthetic Data Generation

Generate realistic sample records for every table in the schema.

Generated data includes:

- Customer information
- Products
- Orders
- Payments
- Appointments
- Transactions
- Employee records
- And much more depending on the selected domain

---

### 🏢 Multiple Application Domains

Supported domains include:

- E-Commerce
- Healthcare
- Banking
- Hospital Management
- School Management
- Library Management
- Food Delivery
- Hotel Booking
- HR Management

Users can also provide custom application domains.

---

### 🎨 Interactive Gradio Interface

A modern web interface built with Gradio allows users to:

- Select application type
- Configure rows per table
- Generate database schemas
- Generate synthetic datasets
- Preview generated data
- Download datasets

---

### 📥 Export Functionality

Generated datasets can be exported as:

- CSV
- JSON
- ZIP Archive

Making them ready for immediate use in applications and data projects.

---

## 🏗️ Architecture

```text
Application Selection
          │
          ▼
   Schema Generator
          │
          ▼
   Database Schema
          │
          ▼
 Synthetic Data Generator
          │
          ▼
 Dataset Preview
          │
          ▼
 Export Dataset
```

---

## 🛠️ Tech Stack

### Frontend

- Gradio

### AI Models

- GPT-OSS-120B (Groq)

### Backend

- Python

### Data Processing

- Pandas
- JSON
- ZIP Utilities

---

## 🔄 Workflow

### Step 1

Select an application domain.

Example:

```text
E-Commerce
```

### Step 2

Specify the number of rows to generate per table.

Example:

```text
20 rows
```

### Step 3

Generate a relational database schema.

Example tables:

```text
customers
products
orders
payments
reviews
```

### Step 4

Generate realistic synthetic records for each table.

### Step 5

Preview generated data directly in the UI.

### Step 6

Download the dataset for use in projects.

---

## 🎯 Example Use Cases

### Software Development

Quickly generate mock databases during development.

### Database Design

Prototype schemas before implementing them in production.

### Machine Learning

Generate synthetic datasets for experimentation.

### Text-to-SQL Research

Create training datasets for:

```text
Natural Language
        ↓
SQL Query Generation
```

### Education

Learn relational database concepts with automatically generated examples.

---

## 🚀 Future Enhancements

- Multi-schema generation
- SQL validation layer
- Text-to-SQL dataset generation
- Parquet export
- Database relationship visualization
- Dataset quality scoring
- Dataset deduplication
- Direct database export (MySQL/PostgreSQL)
- Hugging Face dataset publishing
- Synthetic data benchmarking

---

## 🎯 Project Goal

The goal of this project is to simplify database creation and synthetic data generation using modern AI models while providing an intuitive interface for developers, data engineers, researchers, and students.

By automating schema design and data generation, users can rapidly create realistic datasets without manually designing databases or populating tables.