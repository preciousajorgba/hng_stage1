from fastapi import FastAPI, HTTPException, Body, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import hashlib
import re
from collections import Counter

app = FastAPI(title="String Analyzer API (Beginner-Friendly)", version="1.0")

# -------------------------------------------------------------------
# 🧠 In-memory database (like a temporary storage)
STORE: Dict[str, Dict] = {}

# -------------------------------------------------------------------
# 🕒 Helper function to get the current time
def get_time_now():
    return datetime.utcnow().isoformat() + "Z"

# -------------------------------------------------------------------
# 🔡 Helper function to make things lowercase for comparisons
def normalize(text: str) -> str:
    return text.lower()

# -------------------------------------------------------------------
# 📏 Function to analyze a string and return all its properties
def analyze_string(value: str) -> Dict:
    lower_value = normalize(value)
    length = len(value)
    is_palindrome = lower_value == lower_value[::-1]
    unique_characters = len(set(lower_value))
    word_count = len(re.findall(r"\S+", value))
    sha_hash = hashlib.sha256(lower_value.encode()).hexdigest()
    character_map = dict(Counter(lower_value))

    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha_hash,
        "character_frequency_map": character_map
    }

# -------------------------------------------------------------------
# 🧱 Pydantic models (for validation and Swagger docs)
class StringCreate(BaseModel):
    value: str

class StringProperties(BaseModel):
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str
    character_frequency_map: Dict[str, int]

class StringRecord(BaseModel):
    id: str
    value: str
    properties: StringProperties
    created_at: str

# -------------------------------------------------------------------
# 🧩 Function to apply filters (used in list and natural language endpoints)
def apply_filters(strings: List[Dict],
                  is_palindrome: Optional[bool] = None,
                  min_length: Optional[int] = None,
                  max_length: Optional[int] = None,
                  word_count: Optional[int] = None,
                  contains_character: Optional[str] = None):
    results = []
    for item in strings:
        props = item["properties"]

        if is_palindrome is not None and props["is_palindrome"] != is_palindrome:
            continue
        if min_length is not None and props["length"] < min_length:
            continue
        if max_length is not None and props["length"] > max_length:
            continue
        if word_count is not None and props["word_count"] != word_count:
            continue
        if contains_character:
            ch = normalize(contains_character)
            if ch not in props["character_frequency_map"]:
                continue

        results.append(item)
    return results

# -------------------------------------------------------------------
# 🗣️ Very simple natural language parser (rule-based)
def parse_query(query: str) -> Dict:
    q = query.lower().strip()
    filters = {}

    if "palind" in q:
        filters["is_palindrome"] = True
    if "single word" in q:
        filters["word_count"] = 1
    if match := re.search(r"longer than (\d+)", q):
        filters["min_length"] = int(match.group(1)) + 1
    if match := re.search(r"containing the letter\s+([a-z])", q):
        filters["contains_character"] = match.group(1)
    if "first vowel" in q:
        filters["contains_character"] = "a"

    if not filters:
        raise ValueError("Couldn't understand the query.")
    return filters

# -------------------------------------------------------------------
# 🔍 Find a string record (by value or id)
def find_string(value_or_id: str):
    # Try by hash ID directly
    if re.fullmatch(r"[0-9a-f]{64}", value_or_id):
        return STORE.get(value_or_id)

    # Try by hash of normalized value
    norm = normalize(value_or_id)
    sid = hashlib.sha256(norm.encode()).hexdigest()
    if sid in STORE:
        return STORE[sid]

    # Try direct match (case-insensitive)
    for record in STORE.values():
        if record["value"].lower() == norm:
            return record

    return None

# -------------------------------------------------------------------
# 🚀 Endpoints start here!

# 1️⃣ Create and analyze a string
@app.post("/strings", response_model=StringRecord, status_code=201)
def create_string(data: StringCreate = Body(...)):
    value = data.value

    if not isinstance(value, str):
        raise HTTPException(status_code=422, detail='"value" must be a string')

    props = analyze_string(value)
    sid = props["sha256_hash"]

    if sid in STORE:
        raise HTTPException(status_code=409, detail="String already exists")

    record = {
        "id": sid,
        "value": value,
        "properties": props,
        "created_at": get_time_now()
    }
    STORE[sid] = record
    return record

# 2️⃣ Get all strings (with optional filters)
@app.get("/strings")
def list_strings(
    is_palindrome: Optional[bool] = Query(None),
    min_length: Optional[int] = Query(None),
    max_length: Optional[int] = Query(None),
    word_count: Optional[int] = Query(None),
    contains_character: Optional[str] = Query(None)
):
    if contains_character and len(contains_character) != 1:
        raise HTTPException(status_code=400, detail="contains_character must be one letter")

    results = apply_filters(
        list(STORE.values()),
        is_palindrome,
        min_length,
        max_length,
        word_count,
        contains_character
    )

    return {
        "data": results,
        "count": len(results),
        "filters_applied": {
            k: v for k, v in locals().items() if v is not None and k != "results"
        }
    }

@app.get("/strings/filter-by-natural-language")
def filter_nl(query: str = Query(...)):
    try:
        filters = parse_query(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filtered = apply_filters(list(STORE.values()), **filters)

    return {
        "data": filtered,
        "count": len(filtered),
        "interpreted_query": {
            "original": query,
            "parsed_filters": filters
        }
    }



@app.get("/strings/{string_value}", response_model=StringRecord)
def get_string(string_value: str):
    record = find_string(string_value)
    if not record:
        raise HTTPException(status_code=404, detail="String not found")
    return record

# 4️⃣ Natural language filter
@app.get("/strings/filter-by-natural-language")
def filter_nl(query: str = Query(...)):
    try:
        filters = parse_query(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filtered = apply_filters(list(STORE.values()), **filters)

    return {
        "data": filtered,
        "count": len(filtered),
        "interpreted_query": {
            "original": query,
            "parsed_filters": filters
        }
    }

# 5️⃣ Delete a string
@app.delete("/strings/{string_value}", status_code=204)
def delete_string(string_value: str):
    record = find_string(string_value)
    if not record:
        raise HTTPException(status_code=404, detail="String not found")
    del STORE[record["id"]]
    return JSONResponse(status_code=204, content=None)
