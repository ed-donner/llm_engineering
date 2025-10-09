# 🤖 Synthetic Dataset Generator
## AI-Powered Synthetic Data Generation with Claude 3 Haiku
## 📥 Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/synthetic-dataset-generator.git
cd synthetic-dataset-generator
```

### 2️⃣ Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

**Requirements file (`requirements.txt`):**
```txt
gradio>=4.0.0
anthropic>=0.25.0
pandas>=1.5.0
python-dotenv>=1.0.0
httpx==0.27.2
```

### 4️⃣ Set Up API Key

Create a `.env` file in the project root:

```bash
# .env
ANTHROPIC_API_KEY=your_api_key_here
```

> **Note**: Never commit your `.env` file to version control. Add it to `.gitignore`.

---

## 🚀 Usage

### Running the Application

```bash
python app.ipynb
```

The Gradio interface will launch at `http://localhost:7860`

### Basic Workflow

1. **Enter API Key** (if not in `.env`)
2. **Describe Your Schema** in plain English
3. **Set Number of Records** (1-200)
4. **Add Example Format** (optional, but recommended)
5. **Click Generate** 🎉
6. **Download CSV** when ready

---

## 📝 Example Schemas

### 👥 Customer Data
```
Generate customer data with:
- customer_id (format: CUST-XXXX)
- name (full name)
- email (valid email address)
- age (between 18-80)
- city (US cities)
- purchase_amount (between $10-$1000)
- join_date (dates in 2023-2024)
- subscription_type (Free, Basic, Premium)
```

### 👨‍💼 Employee Records
```
Generate employee records with:
- employee_id (format: EMP001, EMP002, etc.)
- name (full name)
- department (Engineering, Sales, Marketing, HR, Finance)
- salary (between $40,000-$150,000)
- hire_date (between 2020-2024)
- performance_rating (1-5)
- is_remote (true/false)
```

### 🛒 E-commerce Products
```
Generate e-commerce product data with:
- product_id (format: PRD-XXXX)
- product_name (creative product names)
- category (Electronics, Clothing, Home, Books, Sports)
- price (between $5-$500)
- stock_quantity (between 0-1000)
- rating (1.0-5.0)
- num_reviews (0-500)
- in_stock (true/false)
```

---

## 🎯 Advanced Usage

### Batch Generation

For datasets larger than 50 records, the tool automatically:
- Splits generation into batches of 50
- Combines results into a single dataset
- Prevents API timeout issues

### Custom Formats

Provide example JSON to guide the output format:

```json
{
  "id": "USR-001",
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## 🔧 Troubleshooting

### ❌ Error: `proxies` keyword argument

**Solution**: Downgrade httpx to compatible version

```bash
pip install "httpx==0.27.2"
```

Then restart your Python kernel/terminal.

### ❌ API Key Not Found

**Solutions**:
1. Check `.env` file exists in project root
2. Verify `ANTHROPIC_API_KEY` is spelled correctly
3. Ensure no extra spaces in the `.env` file
4. Restart the application after creating `.env`

### ❌ JSON Parsing Error

**Solutions**:
1. Make your schema description more specific
2. Add an example format
3. Reduce the number of records per batch
4. Check your API key has sufficient credits

### ❌ Rate Limit Errors

**Solutions**:
1. Reduce batch size in code (change `batch_size=50` to `batch_size=20`)
2. Add delays between batches
3. Upgrade your Anthropic API plan

---

## 📊 Output Format

### DataFrame Preview
View generated data directly in the browser with scrollable table.

### CSV Download
- Automatic CSV generation
- Proper encoding (UTF-8)
- No index column
- Ready for Excel, Pandas, or any data tool

---

## 🧑‍💻 Skill Level

**Beginner Friendly** ✅

- No ML/AI expertise required
- Basic Python knowledge helpful
- Simple natural language interface
- Pre-configured examples included

---

## 💡 Tips for Best Results

1. **Be Specific**: Include data types, ranges, and formats
2. **Use Examples**: Provide sample JSON for complex schemas
3. **Start Small**: Test with 5-10 records before scaling up
4. **Iterate**: Refine your schema based on initial results
5. **Validate**: Check the first few records before using the entire dataset

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch 
3. Commit your changes 
4. Push to the branch 
5. Open a Pull Request

---


## 🙏 Acknowledgments

- **Anthropic** for the Claude API
- **Gradio** for the UI framework
- **Pandas** for data manipulation

---

## 📞 Support

- 📧 Email: udayslathia16@gmail.com

---

## 🔗 Related Projects

- [Claude API Documentation](https://docs.anthropic.com/)
- [Gradio Documentation](https://gradio.app/docs/)
- [Pandas Documentation](https://pandas.pydata.org/)

---

<div align="center">

**Made with ❤️ using Claude 3 Haiku**

⭐ Star this repo if you find it useful!

</div>