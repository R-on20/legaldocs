# 🧪 How to Run AI Search Tests

## Prerequisites

1. **Install OpenAI library**:
   - Run the `install_openai.bat` file in your project root, OR
   - Manually run: `python -m pip install openai`

2. **Verify your API key**:
   - Your settings.py already has the OpenAI API key configured
   - Make sure you have credits in your OpenAI account

## 🚀 Test Methods

### **Method 1: Django Management Command (Best for testing)**

```bash
# Navigate to your Django project directory
cd C:\Users\User\ILDMS_Project\ILDMS

# Test with a single custom query
python manage.py test_ai_search --query "Show me contracts uploaded last month"

# Run all sample queries
python manage.py test_ai_search --run-samples

# Test a specific legal query
python manage.py test_ai_search --query "Find confidential documents about water supply"

# Test date-based queries
python manage.py test_ai_search --query "Draft legal notices from this year"
```

### **Method 2: Web Interface Test Endpoint**

1. Start your Django server:
```bash
cd C:\Users\User\ILDMS_Project\ILDMS
python manage.py runserver
```

2. Visit these URLs in your browser:
```
http://127.0.0.1:8000/documents/test-ai-search/?q=Show me contracts uploaded last month
http://127.0.0.1:8000/documents/test-ai-search/?q=Find confidential documents
http://127.0.0.1:8000/documents/test-ai-search/?q=Draft legal notices from this year
```

### **Method 3: Live Search in Document List**

1. Start your Django server:
```bash
python manage.py runserver
```

2. Go to the document list page:
```
http://127.0.0.1:8000/documents/documents-list
```

3. Use the search box with natural language queries:
   - "Show me contracts uploaded last month"
   - "Find confidential documents about water supply"
   - "Draft legal notices from this year"
   - "Documents uploaded by john"

## 📊 Sample Test Queries to Try

### Document Type Queries
```
"Show me all contracts"
"Find legal notices"
"Water supply agreements"
"Court filings from this year"
```

### Date-based Queries
```
"Documents uploaded last month"
"Contracts from this year"
"Files uploaded last week"
"Draft documents from yesterday"
```

### Status and User Queries
```
"Approved documents about water rights"
"Draft contracts"
"Confidential documents"
"Documents uploaded by john"
```

### Complex Queries
```
"Show me contracts uploaded by john last month about water supply"
"Find all confidential legal notices from this year"
"Draft agreements about service contracts"
"Approved court filings uploaded last week"
```

## 🔍 What to Look For

### Successful AI Processing
- ✅ Method: `ai`
- ✅ Success: `True`
- ✅ Extracted filters (document_type, date_range, etc.)
- ✅ Keywords found
- ✅ AI badge in web interface

### Fallback to Keyword Search
- ⚠️ Method: `fallback`
- ⚠️ Success: `True` (but using keywords only)
- ⚠️ Warning badge in web interface

### AI Search Disabled/Failed
- ❌ Method: `unknown` or error message
- ❌ Success: `False`
- ❌ Check API key and internet connection

## 🛠️ Troubleshooting

### If AI Search is Disabled
1. Check your OpenAI API key in settings.py
2. Verify you have OpenAI credits
3. Check internet connection
4. Install openai library: `pip install openai`

### If Getting Fallback Results
- This is normal - the system falls back to keyword search
- Check the AI response for parsing errors
- Try simpler, clearer queries

### If No Results Found
- Make sure you have documents in your database
- Check document permissions (confidential docs need permissions)
- Try broader queries first

## 📝 Example Command Output

```bash
C:\Users\User\ILDMS_Project\ILDMS> python manage.py test_ai_search --query "contracts from last month"

AI Search Enabled: True

Testing query: 'contracts from last month'
--------------------------------------------------
Method: ai
Success: True
Extracted Filters:
  document_type: CONTRACT
  uploaded_after: 2025-06-28
Keywords: contracts, month
AI Response:
{
  "document_type": "CONTRACT",
  "date_range": {
    "relative": "last_month"
  },
  "keywords": ["contracts", "month"]
}
```

## 🎯 Quick Start Commands

```bash
# 1. Install dependency
python -m pip install openai

# 2. Navigate to Django project
cd C:\Users\User\ILDMS_Project\ILDMS

# 3. Test AI search with samples
python manage.py test_ai_search --run-samples

# 4. Test a specific query
python manage.py test_ai_search --query "Show me contracts from last month"

# 5. Start server and test in browser
python manage.py runserver
# Then visit: http://127.0.0.1:8000/documents/documents-list
```
