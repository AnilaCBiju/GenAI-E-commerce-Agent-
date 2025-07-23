# GenAI-E-commerce-Agent-

An AI-powered agent that answers natural language questions on e-commerce datasets using Google Gemini, FastAPI, SQL, and LangChain. Bonus features include chart generation and optional streaming.


---
 Datasets

1. **Ad Sales** — Cost, clicks, conversions, CPC, etc.
2. **Total Sales** — Units ordered, item-wise sales, etc.
3. **Eligibility** — Item eligibility metadata

---

##  Features

-  Converts user questions to SQL using Gemini LLM via LangChain
-  Auto-generates accurate answers to questions like:
  - "What is my total sales?"
  - "Calculate the RoAS"
  - "Which product had the highest CPC?"

---

##  How to Run

    ```bash
        pip install -r requirements.txt

## Run the server
  
      uvicorn main:app --reload
The app will be live at: http://127.0.0.1:8000


LLM Used:Gemini 2.5 Flash from Google AI Studio
Make sure to add your API key inside main.py under google_api_key="..."

