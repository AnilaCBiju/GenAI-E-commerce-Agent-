from fastapi import FastAPI, Query

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pandas as pd
import sqlite3
import plotly.express as px

from langchain_community.utilities import SQLDatabase
from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_google_genai import ChatGoogleGenerativeAI

#  Step 1: Load CSVs into SQLite (only run once if needed)
conn = sqlite3.connect("ecommerce.db")
df1 = pd.read_csv("data/ad_sales.csv")
df2 = pd.read_csv("data/total_sales.csv")
df3 = pd.read_csv("data/eligibility.csv")

df1.to_sql("ad_sales", conn, if_exists="replace", index=False)
df2.to_sql("total_sales", conn, if_exists="replace", index=False)
df3.to_sql("eligibility", conn, if_exists="replace", index=False)
conn.close() 

# Step 2: Set up LLM and SQL database
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key="AI****************************************Q",
    temperature=0
)

db = SQLDatabase.from_uri("sqlite:///ecommerce.db")
chain = create_sql_query_chain(llm, db)

# Step 3: FastAPI App
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the E-commerce AI Agent!"}

# Step 4: AI Ask Endpoint
import re  # required for cleaning the SQL

@app.get("/ask")
def ask(query: str):
    try:
        raw_sql = chain.invoke({"question": query})
        print("🔎 Raw SQL from LLM:", raw_sql)

        # Clean SQL string
        cleaned_sql = re.sub(r"(?i)Question:.*", "", raw_sql)
        cleaned_sql = re.sub(r"(?i).*SQLQuery:\s*", "", cleaned_sql).strip()
        cleaned_sql = re.sub(r"```(?:sql)?", "", cleaned_sql).replace("```", "").strip()

        print("✅ Cleaned SQL:", cleaned_sql)

        # Execute SQL
        conn = sqlite3.connect("ecommerce.db")
        cursor = conn.execute(cleaned_sql)
        result = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        conn.close()

        result_data = [dict(zip(col_names, row)) for row in result]

        return {
            "question": query,
            "sql_query": cleaned_sql,
            "result": result_data
        }

    except Exception as e:
        return {
            "question": query,
            "sql_query": cleaned_sql if 'cleaned_sql' in locals() else None,
            "error": str(e)
        }

