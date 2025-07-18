from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from typing import Optional

app = FastAPI()

def init_db():
    conn = sqlite3.connect('reviews.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class ReviewRequest(BaseModel):
    text: str

class ReviewResponse(BaseModel):
    id: int
    text: str
    sentiment: str
    created_at: str

def analyze_sentiment(text: str) -> str:
    text_lower = text.lower()
    positive_words = ['хорош', 'отличн', 'прекрасн', 'любл', 'нравит', 'супер']
    negative_words = ['плох', 'ужасн', 'ненавиж', 'отвратительн', 'кошмар']
    
    for word in positive_words:
        if word in text_lower:
            return 'positive'
    
    for word in negative_words:
        if word in text_lower:
            return 'negative'
    
    return 'neutral'

@app.post("/reviews", response_model=ReviewResponse)
async def create_review(review: ReviewRequest):
    sentiment = analyze_sentiment(review.text)
    created_at = datetime.utcnow().isoformat()
    
    conn = sqlite3.connect('reviews.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
        (review.text, sentiment, created_at)
    )
    review_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute(
        "SELECT id, text, sentiment, created_at FROM reviews WHERE id = ?",
        (review_id,)
    )
    review_data = cursor.fetchone()
    conn.close()
    
    if not review_data:
        raise HTTPException(status_code=500, detail="Failed to create review")
    
    return ReviewResponse(
        id=review_data[0],
        text=review_data[1],
        sentiment=review_data[2],
        created_at=review_data[3]
    )

@app.get("/reviews", response_model=list[ReviewResponse])
async def get_reviews(sentiment: Optional[str] = None):
    conn = sqlite3.connect('reviews.db')
    cursor = conn.cursor()
    
    if sentiment:
        cursor.execute(
            "SELECT id, text, sentiment, created_at FROM reviews WHERE sentiment = ?",
            (sentiment,)
        )
    else:
        cursor.execute(
            "SELECT id, text, sentiment, created_at FROM reviews"
        )
    
    reviews = cursor.fetchall()
    conn.close()
    
    return [
        ReviewResponse(
            id=row[0],
            text=row[1],
            sentiment=row[2],
            created_at=row[3]
        ) for row in reviews
    ]
