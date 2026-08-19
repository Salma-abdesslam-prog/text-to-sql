# 🔍 Text → SQL

Convert natural language questions into SQL queries using open-source LLMs (GPT-OSS, Qwen) via the **Groq API**.

Includes a built-in **SQLite test database** (e-commerce schema) so you can generate and execute queries immediately — no database setup required.

---

## ✨ Features

- 🤖 Open-source LLMs via **Groq** (GPT-OSS 120B, GPT-OSS 20B, Qwen3.6) — free tier available
- 🧪 Built-in test database with realistic e-commerce data
- 🐬 Connect to your own **MySQL** database
- ▶️ Execute generated queries and see results instantly
- 🕓 Query history panel
- 🚀 One-click deploy on **Streamlit Cloud**

---

## 🗄️ Test Database Schema

The bundled SQLite test database (`data/test_store.db`) contains:

| Table | Description |
|-------|------------|
| `customers` | 10 customers from different countries |
| `categories` | 5 product categories |
| `products` | 12 products with prices and stock |
| `orders` | 12 orders with statuses |
| `order_items` | Line items linking orders to products |

### Example questions to try

- *"Show me the top 5 customers by total spending"*
- *"Which products are out of stock?"*
- *"What is the average order value per country?"*
- *"List all delivered orders with customer names"*
- *"Show the 3 best-selling products by quantity sold"*
- *"Which customers have never placed an order?"*

---

## 🚀 Quick Start (local)

```bash
# 1. Clone the repo
git clone https://github.com/your-username/text-to-sql.git
cd text-to-sql

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Groq API key
cp .env.example .env
# Edit .env and paste your key from https://console.groq.com

# 4. Launch the app
streamlit run app.py
```

---

## ☁️ Deploy on Streamlit Cloud (free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo and select `app.py`
4. Add your **Groq API key** as a secret:
   - Key: `GROQ_API_KEY`
   - Value: `gsk_...`
5. Click **Deploy** — done!

### Public demo mode

For a link you can share publicly (e.g. on a CV/portfolio), add a second secret to switch on demo mode:

- Key: `APP_DEMO_MODE`
- Value: `true`

This hides the "connect your own MySQL server" form (visitors only get the bundled sample database) and lets visitors try the app immediately using your shared `GROQ_API_KEY` — they can still paste their own key in the sidebar to use their own quota instead. Your key is only ever used server-side; it's never sent to the browser.

---

## 🏗️ Project Structure

```
text-to-sql/
├── app.py                    # Streamlit UI
├── core/
│   ├── llm_client.py         # Groq API wrapper
│   ├── prompt_builder.py     # System & user prompt templates
│   ├── sql_validator.py      # SQL cleaning & safety checks
│   └── text_to_sql.py        # Main pipeline
├── db/
│   ├── connector.py          # SQLite / MySQL engine factory
│   ├── schema_extractor.py   # Auto-extract DB schema for prompts
│   └── query_executor.py     # Safe query execution → DataFrame
├── data/
│   └── init_db.py            # Test database initialization
├── .streamlit/
│   └── config.toml           # Streamlit theme
├── requirements.txt
└── .env.example
```

---

## 🔑 Getting a Free Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Create an API key
4. Paste it in the sidebar or in `.env`

---

## ⚠️ Security Notes

- Only **SELECT** queries are allowed (enforced by the validator)
- Never commit your `.env` file
- For production, use read-only database credentials
