# AI-Powered Human Identification System

> Final Year Project — BS Computer Science  
> Karakoram International University, Gilgit Baltistan

---

## What This System Does

A web platform that connects missing persons reports 
with unidentified individual records using AI face 
matching and multimodal similarity scoring.

**The Problem:**  
In Pakistan, families report missing persons at police 
stations while hospitals admit unidentified patients. 
These records exist in separate systems with no 
connection between them. Cases go unsolved for weeks.

**The Solution:**  
When any report is submitted, the system automatically 
compares it against all records from the other side 
and returns ranked potential matches with confidence 
scores.

---

## How It Works
Photo uploaded

↓

FaceNet extracts 128-number face embedding

↓

Combined with age, location, description scoring

↓

Cosine similarity against all database records

↓

Top matches returned with confidence percentage

---

## Multimodal Scoring

| Signal | Weight | Method |
|--------|--------|--------|
| Face similarity | 70% | FaceNet + cosine similarity |
| Description | 10% | SentenceTransformers NLP |
| Age proximity | 10% | Normalized difference |
| Gender match | 5% | Binary comparison |
| Location | 5% | Geographic distance |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js + Tailwind CSS |
| Backend | Python + Flask |
| AI Model | DeepFace + FaceNet |
| NLP | SentenceTransformers |
| Database | SQLite |
| Auth | JWT + bcrypt |

---

## Portals

**Public** — Search by face, track case status  
**Family/Anyone** — Report missing person (no login)  
**Hospital** — Report unidentified patient (login required)  
**Admin** — Full case management dashboard  

---

## Project Structure
ai-identification-system/

├── Notebooks/          # Colab AI prototyping (Days 1-7)

├── backend/            # Python Flask API

│   ├── routes/         # API endpoints

│   ├── services/       # AI and matching logic

│   ├── middleware/     # JWT authentication

│   └── uploads/        # Stored photos

└── frontend/           # Next.js (coming soon)

---

## Development Progress

- [x] Day 1-7: AI engine proven in Google Colab
- [x] Day 8: Flask backend structure
- [x] Day 9: JWT authentication
- [ ] Day 10: Core API routes
- [ ] Day 11-12: Next.js frontend
- [ ] Day 13-14: Testing and evaluation

---

## Dataset

- Development: 50-100 manually collected photos
- Evaluation: LFW (Labeled Faces in the Wild)
- Metrics: Precision, Recall, F1 Score

---

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

---

## Supervisor
Mam Gul Gabeen — KIU Computer Science Department
