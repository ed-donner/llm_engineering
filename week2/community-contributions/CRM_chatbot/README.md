Github: https://github.com/Bahadir-OZCANLI
Linkedin: https://www.linkedin.com/in/bahadir-ozcanli-56b94523b/

# Customer Relation Chatbot

A conversational AI chatbot for a boutique clothing store that assists customers with product inquiries, order management, and customer data collection. Built with OpenAI's GPT-4o-mini model and Gradio for the user interface.

## Features

- **Product Price Inquiry**: Get real-time pricing information for available products
- **Order Status Tracking**: Check the current status of customer orders
- **Order Placement**: Place new orders for customers
- **Customer Data Management**: Collect and save customer contact information
- **Natural Language Interaction**: Conversational interface powered by OpenAI's language model
- **Database Integration**: SQLite database for persistent data storage

## Prerequisites

- Python 3.7+
- OpenAI API key
- Required Python packages:
  - `openai`
  - `gradio`
  - `python-dotenv`
  - `sqlite3` (included in Python standard library)

## Installation

1. Clone or navigate to the project directory:
```bash
cd /path/to/chatbot_CRM
```

2. Install required packages:
```bash
pip install openai gradio python-dotenv
```

3. Set up your environment variables:
   - Create a `.env` file in the project directory
   - Add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Database Setup

Before running the chatbot, you need to set up the database:

1. Run the `db_process.ipynb` notebook to:
   - Create the database schema (customers, products, orders tables)
   - Insert sample data

The database schema includes:
- **customers**: Stores customer contact information (id, first_name, last_name, phone, mail)
- **products**: Stores product catalog (id, product_name, price, stock_count)
- **orders**: Stores order information (id, customer_id, product_id, order_status, order_date)

## Configuration

The chatbot uses the following default settings (configurable in the notebook):
- **Database**: `customer_relation.db`
- **Model**: `gpt-4o-mini`
- **Available Products**: shirt, skirt, jeans, socks

## Usage

1. Ensure the database is set up (run `db_process.ipynb` first)
2. Open and run `customer_relation.ipynb`
3. The Gradio interface will launch automatically
4. Interact with the chatbot through the web interface

The chatbot will be available at `http://127.0.0.1:7863` (or another port if 7863 is occupied).

## Available Functions

The chatbot has access to the following tools:

### 1. `get_price(product_name)`
Retrieves the price of a specified product from the database.

### 2. `get_order_status(order_id)`
Checks the current status of an order by its ID.

### 3. `take_order(product_name, customer_id)`
Places a new order for a customer. Creates a new order record with "pending" status.

### 4. `save_customer_data(first_name, last_name, phone, mail)`
Saves new customer contact information to the database.

## Example Interactions

The chatbot can handle various customer queries:

- "I want to buy a shirt"
- "I want to know the price of the shirt"
- "I want to know the status of my order with id 1253"
- "I want to save my contact information"

## System Behavior

The chatbot is configured to:
- Act as a professional sales assistant
- Provide short, courteous responses (max 3 sentences)
- Proactively collect customer data when appropriate
- Direct customers to place orders
- Use available tools automatically when needed
- Handle tool calls in a loop until a final response is generated

## Notes

- The chatbot uses OpenAI's function calling feature to interact with the database
- All database operations are logged to the console for debugging
- The chatbot maintains conversation history during the session
- Order statuses can be: "pending", "preparing", "on delivery", "delivered", "transfer"

## Troubleshooting

- **API Key Error**: Ensure your `.env` file contains a valid `OPENAI_API_KEY`
- **Database Not Found**: Run `db_process.ipynb` first to create and populate the database
- **Port Already in Use**: Gradio will automatically use the next available port

## License

This project is part of the LLM Engineering course materials.