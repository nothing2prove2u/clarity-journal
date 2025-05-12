from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime
import os, openai
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from openai import OpenAI
client = OpenAI()
import re

def analyze_entry(text: str) -> str:
    """
    Call OpenAI and return a SHORT, 5-section reflection
    (psycho-social, linguistic, archetypal).
    """
    prompt = f""""
You are **Clarity Mentor**, blending positive-psychology, discourse analysis, and Jungian insight.  
I'll send a journal entry wrapped in <ENTRY> tags.

**Goal** - In ≤ 200 words, hold up a clear mirror so I can see how my mind works. No advice-giving or “fixes,” just revealing patterns.

**Deliver exactly five labelled blocks (keep labels bold):**

1. **Mood Pulse** - 2-3 adjectives that distil the emotional flavour.  
2. **Core Storylines** - Up to 3 brief quotes (≤ 10 words each) followed by a one-line reading of what each wording hints about my assumptions or focus.  
3. **Thinking Loops** - One sentence naming the dominant cognitive pattern you detect (e.g., future-forecasting, self-comparison).  
4. **Archetype in Play** - Name the Jungian archetype most evident and give a one-sentence link to the entry.  
5. **Hidden Currents** - Two crisp observations of strengths, resources, or tensions running beneath the surface.

End with one open question (≤ 15 words) that could spark deeper self-reflection.  
Write in plain Markdown; labels bold, content normal text.  
Stay friendly, concise, insight-rich—no more than 200 words total.

<ENTRY>  
{text}  
</ENTRY>

""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",                 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=260           
    )
    
    try:
        insight_md = response.choices[0].message.content.strip()
    except (AttributeError, IndexError):
        insight_md = ""
    return insight_md


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']            = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']     = False
db = SQLAlchemy(app)

class JournalEntry(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    content    = db.Column(db.Text, nullable=False)
    insight    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    text = request.form["entry"]
    insight = analyze_entry(text) or ""
    print("DEBUG insight >>>", repr(insight))
    entry = JournalEntry(content=text, insight=insight)
    db.session.add(entry)
    db.session.commit()
    return redirect(url_for('list_entries'))

@app.route("/entries")
def list_entries():
    entries = (JournalEntry.query
               .order_by(JournalEntry.created_at.desc())
               .all())
    return render_template("entries.html", entries=entries)

if __name__ == "__main__":
    app.run(debug=False)