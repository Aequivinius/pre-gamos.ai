import json

INPUT_LIMIT = 10000

LANGUAGES = {
    "English": "EN",
    "Spanish": "ES",
    "Italian": "IT",
    "German": "DE",
    "Japanese": "JP",
}

PERSONAE = {
    "Teenager": "👶",
    "Adult Layperson": "🧑",
    "University Student in Biomedicine": "🧑‍🎓",
    "Professional Clinician": "🧑‍⚕️",
}

LENGTHS = ["extremely short", "short", "long"]


CHARACTERISTICS = {
    "Teenager": "for a 15-year old child, using simple language and avoiding any technical terms, or complicated words or abbreviations",
    "Adult Layperson": "for an adult layperson, avoiding biomedical terms, but using a language suitable to adults",
    "University Student in Biomedicine": "for a university student in biomedicine",
    "Professional Clinician": "for a professional clinician, making heavy use of technical terms, complicated language and assuming they already have deep previous knowledge",
}

PAPERS = {}
with open("papers.json") as f:
    PAPERS = json.load(f)
