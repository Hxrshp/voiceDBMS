# VoiceDBMS 🎙️
### Translate Plain English spoken commands into SQL & execute them locally.

VoiceDBMS is a modular Python utility, terminal-based CLI, and database wrapper designed to bridge the gap between human language and relational databases. Users can search, insert, update, or delete records in plain English—no SQL knowledge required.

It runs **100% offline out-of-the-box** using a custom regular expression parsing engine, with built-in extensions for **Google Gemini API** and **Ollama (Llama 3)**.

---

## 🚀 Key Features

* **Dual Input Modes**: Run queries by speaking into your microphone or typing directly.
* **Transcription Confirmation & Editing**: Prompts verification (`Did I get that right?`) to correct voice capture errors before database mutation occurs.
* **Offline Fallback Parser**: Robust regex compiler translates common operations (SELECT, SELECT-WHERE, INSERT, UPDATE, DELETE) without internet or LLM setup.
* **Developer Integration**: Core functions `generate_sql` and `run_query` can be imported directly into other scripts/applications.
* **ASCII Layout Output**: Select results are formatted into clean column-adjusted console tables.
* **Local Persistence**: Saves a rolling history of the last 5 executed requests in a `.query_history.json` file.

---

## 🛠️ Architecture Flowchart

```
           [ Voice Input / Mic ]      [ Text Input ]
                     │                      │
                     ▼                      ▼
           [ Speech Recognition ]           │
                     │                      │
                     ▼                      ▼
           [ Transcript Confirmation / Edit Prompt ]
                                │
                                ▼
                   [ sql_generator.generate_sql() ]
                                │
      ┌─────────────────────────┼─────────────────────────┐
      ▼ (Check API Key)         ▼ (Check Ollama)          ▼ (Offline Default)
 [ Gemini 1.5 Flash ]     [ Ollama / Llama 3 ]      [ Regex Parser Engine ]
      │                         │                         │
      └─────────────────────────┼─────────────────────────┘
                                │
                                ▼
                     [ SQLite Database Execution ]
                                │
                                ▼
                   [ Print ASCII Table Output ]
```

---

## 💻 Quick Setup

### 1. Prerequisites
Clone the repository and install requirements:
```bash
git clone https://github.com/your-username/voiceDBMS.git
cd voiceDBMS
pip install -r requirements.txt
```

### 2. Seed Mock Database Records
Creates a local SQLite database file `sample.db` pre-populated with mock customer data:
```bash
python database_setup.py
```

### 3. Optional: Configure Gemini AI Key
Copy the template environment file to `.env`:
```bash
copy .env.example .env
```
Open `.env` and paste your free key from Google AI Studio:
```env
GEMINI_API_KEY=your_key_here
```

### 4. Launch the CLI Tool
```bash
python main.py
```

---

## 📖 Developer API Usage (Integration)

You can easily integrate VoiceDBMS into your own codebase:

```python
from sql_generator import generate_sql
from database_query import run_query

# 1. Translate a natural sentence to SQL
sql = generate_sql("change the city of rahul to pune")
print("SQL:", sql) 
# SQL: UPDATE customers SET city = 'Pune' WHERE name = 'Rahul';

# 2. Run query and get results + headers
rows, headers = run_query(sql)
print("Headers:", headers)
print("Rows:", rows)
```

---

## 🧘 The Vibe Coding Journey (How This Was Built)

This project was built entirely using **Vibe Coding**—the modern developer superpower of prompting AI coding assistants, setting up design principles, and structuring logic through chat. 

No manual line-by-line coding was harmed in the making of this project. Instead, the developer navigated:
* Initializing local SQLite structures.
* Handling microphone transcription speech errors.
* Running out-of-the-box offline regex parsers.
* Integrating Google's `gemini-3.6-flash` API.
* Handling complex `JOIN`s, schema introspections, and real-time database view refreshes.

If this project works beautifully, credit goes to the vibe. If something breaks, please adjust your prompts and try again! 🚀

---

## 📄 License
This project is open-source and licensed under the MIT License.