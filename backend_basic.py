from fastapi import FastAPI,HTTPException
import uuid
import requests
from datetime import datetime
import sqlite3

DEEPSEEK_API_KEY="sk-e4a3846d6f064c17988d59f4900aefa7"
MAX_TOKENS=15000

app=FastAPI()

def init_db():
    conn=sqlite3.connect("tokens.db")
    cursor=conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS tokens (
    token TEXT PRIMARY KEY,
    used INTEGER,
    max INTEGER,
    month TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

def get_token_info(token):
    conn=sqlite3.connect("tokens.db")
    cursor=conn.cursor()
    cursor.execute("SELECT token, used, max, month FROM tokens WHERE token = ?",(token,))
    row=cursor.fetchone()
    conn.close()
    return row

def update_token(token,used,month):
    conn=sqlite3.connect("tokens.db")
    cursor=conn.cursor
    cursor.execute("UPDATE tokens SET used = ?, month = ? WHERE token = ?",(used,month,token))
    conn.commit()
    conn.close()

@app.get("/generate_link")
def generate_link():
    """Generate a token with monthly quota."""
    token=str(uuid.uuid4())
    current_month=datetime.now().strftime("%Y-%m")
    conn=sqlite3.connect("tokens.db")
    cursor.execute("INSERT INTO tokens (token, used, max, month) VALUES (?, ?, ?, ?)",(token, 0, MAX_TOKENS, current_month))
    conn.commit()
    conn.close()
    return {"token":token}
@app.post("/ask")
def ask(token:str,question:str,tokens_used:int):
    if token not in tokens:
        raise HTTPException(status_code=400,detail="Invalid or expired token")
    _, used, max_tokens, month=token_info
    current_month=datetime.now().strftime("%Y-%m")
    if month != current_month:
        used=0
        month=current_month
    remaining=max_tokens-used
    if remaining<=0:
        raise HTTPException(status_code=403,detail="Quota exceeded")
    if tokens_used>remaining:
        raise HTTPException(status_code=403,detail="Token quota will be exceeded with this query")
    response=requests.post("https://api.deepseek.com/chat/completions",headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type":"application/json"},
    json={
        "model":"deepseek-chat",
        "messages":[
            {"role":"system","content":"You are a helpful assistant."},
            {"role":"user","content":question}
        ]
    })
    if response.status_code!=200:
        raise HTTPException(status_code=500,detail=f"Deepseek error:{response.text}")
    data=response.json()
    deepseek_answer=data["choices"][0]["message"]["content"]
    used+=tokens_used
    update_token(token,used,month)
    return {
        "answer":deepseek_answer,
        "remaining":remaining
    }