# 📦 Inventory Agent  

Python-based Inventory Agent using **Gemini API** to analyze sales & stock data across cities, calculate reorder points, and generate **AI-powered recommendations**.  

---

## 📁 Project Structure  
```
.
├── .env              # Gemini API key
├── meta.json         # Lead time & manufacturing config
├── requirements.txt  # Python dependencies
├── run_agent.py      # Main script
├── Sales.csv         # Sales data
└── Stock.csv         # Current stock levels
```

---

## 🔑 Setup  

1. **Environment File (`.env`)**  
   Add your Gemini API key:  
   ```ini
   GEMINI_API_KEY=YOUR_KEY_HERE
   ```

2. **Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration (`meta.json`)  
```json
{
  "lead_time_days": {
    "SKU-1": 5,
    "SKU-2": 3,
    "SKU-3": 7,
    "SKU-4": 4,
    "SKU-5": 2,
    "SKU-6": 3,
    "SKU-7": 1,
    "SKU-8": 4,
    "SKU-9": 6,
    "SKU-10": 4
  },
  "manufacturing_batch_size": 100
}
```
- **lead_time_days** → Order lead time per SKU  
- **manufacturing_batch_size** → Minimum order qty  

---

## 🚀 Run Agent  

```bash
python run_agent.py
```

### User Inputs  
- **Product ID** (e.g., `SKU-5`)  
- **City selection** (from numbered list)  

---

## 📊 Output  

- **Inventory Summary** (stock, sales, avg daily sales)  
- **City Report JSON** → `inventory_report_<sku>_<city>.json`  
- **AI Recommendation** (reorder need + suggested units)  

---

