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
    model="gemini-1.5-flash",
    google_api_key="AIz******************************************Q",
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
        # Step 1: Use the LLM to generate SQL query
        raw_sql = chain.invoke({"question": query})

        # Step 2: Extract SQL query only (remove markdown/code block or LLM prefixes)
        cleaned_sql = re.sub(r"```(?:sql|sqlite)?\s*([\s\S]+?)```", r"\1", raw_sql).strip()
        cleaned_sql = re.sub(r"^(SQLQuery:|ite)?\s*", "", cleaned_sql).strip()

        # Step 3: Print to terminal (debug only)
        print("🔎 Raw SQL:", raw_sql)
        print("✅ Cleaned SQL:", cleaned_sql)

        # Step 4: Execute the SQL query
        conn = sqlite3.connect("ecommerce.db")
        cursor = conn.execute(cleaned_sql)
        result = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        conn.close()

        # Step 5: Format as JSON-friendly
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


#  Step 5: Chart Endpoint (thread-safe)
@app.get("/chart", response_class=HTMLResponse)
def sales_chart(query: str = Query(..., description="User's natural language question")):
    import sqlite3
    import re

    # Step 1: Use LLM to generate SQL
    raw_sql = chain.invoke({"question": query})

    # Step 2: Clean the SQL (remove markdown/code block or LLM prefixes)
    cleaned_sql = re.sub(r"```(?:sql|sqlite)?\s*([\s\S]+?)```", r"\1", raw_sql).strip()
    cleaned_sql = re.sub(r"^(SQLQuery:|ite)?\s*", "", cleaned_sql).strip()

    # Debugging (optional)
    print(" LLM Output:", raw_sql)
    print(" Cleaned SQL:", cleaned_sql)

    # Step 3: Run SQL
    try:
        conn = sqlite3.connect("ecommerce.db")
        df = pd.read_sql_query(cleaned_sql, conn)
        conn.close()
    except Exception as e:
        return HTMLResponse(content=f"<h2>SQL Error:<br>{query}<br><br>{e}</h2>", status_code=500)

    # Step 4: Auto-plot chart
    try:
        if len(df.columns) < 2:
            return HTMLResponse(content=f"<h2>Need at least 2 columns to plot a chart</h2>", status_code=400)

        fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=f"Chart for: {query}")
        html_chart = fig.to_html(full_html=False)
        return f"<html><body>{html_chart}</body></html>"

    except Exception as e:
        return HTMLResponse(content=f"<h2>Charting Error:<br>{e}</h2>", status_code=500)
