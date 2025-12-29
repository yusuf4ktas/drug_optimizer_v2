from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from optimizer import DrugOptimizer

# --- NLP Setup ---
try:
    from transformers import pipeline

    nlp_pipeline = pipeline("ner", model="d4data/biomedical-ner-all", aggregation_strategy="simple")
except:
    nlp_pipeline = None
    print("Warning: Transformers not installed. NLP endpoint will fail.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = 'drug_project.db'
optimizer_engine = DrugOptimizer(DB_PATH)


# --- Data Models ---
class OptimizeRequest(BaseModel):
    conditions: List[str]
    mode: str = "ilp"  # Options: 'ilp', 'greedy'


class TextRequest(BaseModel):
    text: str
    mode: str = "ilp"


# --- Database Helpers ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_list_data(conn, drug_id, table, column):
    """Helper to fetch simple lists like synonyms."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT {column} FROM {table} WHERE drugbank_id = ?", (drug_id,))
    return [row[0] for row in cursor.fetchall()]


def enrich_details(drug_id, basic_info):
    """
    Fetches extra details for the UI, including new metabolic info.
    """
    conn = get_db_connection()
    try:
        # 1. Synonyms
        basic_info['synonyms'] = get_list_data(conn, drug_id, 'synonyms', 'synonym')[:5]

        # 2. Food Interactions
        basic_info['food_interactions'] = get_list_data(conn, drug_id, 'food_interactions', 'interaction_text')

        # 3. Dosages
        c = conn.cursor()
        c.execute("SELECT form, route, strength FROM dosages WHERE drugbank_id = ? LIMIT 5", (drug_id,))
        basic_info['dosages'] = [dict(row) for row in c.fetchall()]

        # 4. Pathways
        basic_info['pathways'] = get_list_data(conn, drug_id, 'pathways', 'pathway_name')

        # 5. Enzymes
        # Crucial for explaining metabolic risks
        c.execute("""
                  SELECT enzyme_name, action, inhibition_strength, induction_strength
                  FROM enzymes
                  WHERE drugbank_id = ?
                    AND (organism = 'Humans'
                     OR organism IS NULL)
                      LIMIT 5
                  """, (drug_id,))
        basic_info['enzymes'] = [dict(row) for row in c.fetchall()]

        # 6. Targets
        c.execute("""
                  SELECT target_name, known_action
                  FROM targets
                  WHERE drugbank_id = ?
                    AND (organism = 'Humans' OR organism IS NULL) LIMIT 5
                  """, (drug_id,))
        basic_info['targets'] = [dict(row) for row in c.fetchall()]

    finally:
        conn.close()
    return basic_info


def merge_subwords(results):
    """
    Reconstructs words split by the tokenizer (e.g., 'stomach' + '##ache' -> 'stomachache').
    Handles label conflicts by prioritizing medical conditions over body parts.
    """
    if not results:
        return []

    merged = []

    PRIORITY_LABELS = {'Disease_disorder', 'Sign_symptom'}

    current_word = results[0]

    for next_word in results[1:]:
        # Check if the next token is a subword (starts with ##) OR is immediately adjacent
        is_subword = next_word['word'].startswith('##')
        is_adjacent = next_word['start'] == current_word['end']

        if is_subword or is_adjacent:
            clean_suffix = next_word['word'].replace('##', '')
            current_word['word'] += clean_suffix
            current_word['end'] = next_word['end']

            current_word['score'] = (current_word['score'] + next_word['score']) / 2

            # Label Logic: If the suffix implies a disorder (e.g., ##ache is 'Sign_symptom'),
            # override the 'Biological_structure' label of the prefix.
            if next_word['entity_group'] in PRIORITY_LABELS:
                current_word['entity_group'] = next_word['entity_group']
        else:
            merged.append(current_word)
            current_word = next_word

    merged.append(current_word)
    return merged


# --- Endpoints ---

@app.post("/optimize")
def optimize_regimen(req: OptimizeRequest):
    """
    Main endpoint. Switches between ILP (Precise) and Greedy (Fast).
    """
    print(f"Received request: {req.conditions} (Mode: {req.mode})")

    # Choose Algorithm
    if req.mode.lower() == 'greedy':
        result = optimizer_engine.solve_greedy(req.conditions)
    else:
        result = optimizer_engine.solve_ilp(req.conditions)

    # Enrich Result with DB Details
    final_regimen = []
    for drug in result['regimen']:
        enriched = enrich_details(drug['id'], drug)
        final_regimen.append(enriched)

    result['regimen'] = final_regimen
    return result


@app.post("/optimize/text")
def optimize_text(req: TextRequest):
    """
    Extracts entities, reconstructs fragmented words, filters context, and optimizes.
    """
    if not nlp_pipeline:
        raise HTTPException(status_code=503, detail="NLP Model not available.")

    # Get Raw Results
    results = nlp_pipeline(req.text)

    # Merge Fragmented Tokens (Fixes 'stomach' + '##ache')
    merged_results = merge_subwords(results)

    # Filter for Relevant Conditions
    TARGET_LABELS = {'Disease_disorder', 'Sign_symptom', 'Diagnostic_procedure'}

    entities = set()
    print(f"DEBUG: Processing {len(merged_results)} potential entities...")

    for entity in merged_results:
        label = entity['entity_group']
        word = entity['word']
        score = entity['score']

        if score > 0.5 and label in TARGET_LABELS:
            clean_word = word.strip()
            if len(clean_word) > 2:
                entities.add(clean_word)
                print(f" -> KEEP: {clean_word} ({label}, {score:.2f})")
        else:
            print(f" -> SKIP: {word} ({label}, {score:.2f})")

    cleaned_entities = list(entities)

    if not cleaned_entities:
        return {
            "status": "No Medical Conditions Found",
            "message": "Entities found were either non-medical (dates, frequency) or low confidence.",
            "regimen": []
        }

    # Optimization
    if req.mode.lower() == 'greedy':
        result = optimizer_engine.solve_greedy(cleaned_entities)
    else:
        result = optimizer_engine.solve_ilp(cleaned_entities)

    # Enrichment
    final_regimen = []
    for drug in result['regimen']:
        enriched = enrich_details(drug['id'], drug)
        final_regimen.append(enriched)

    result['regimen'] = final_regimen
    result['nlp_source_entities'] = cleaned_entities
    return result

@app.post("/graph")
def get_graph(req: OptimizeRequest):
    """
    Generates nodes/links for visualization.
    Uses the optimizer's internal candidate fetcher to map Conditions -> Drugs.
    """
    candidates, coverage, drug_info = optimizer_engine._fetch_candidates(req.conditions)

    nodes = []
    links = []
    existing_nodes = set()

    # Condition Nodes
    for c in req.conditions:
        if c not in existing_nodes:
            nodes.append({"id": c, "name": c, "group": "condition"})
            existing_nodes.add(c)

        # Links: Condition -> Drug
        for d_id in coverage[c]:
            links.append({"source": c, "target": d_id, "value": 1})

    # Drug Nodes
    for d_id, info in drug_info.items():
        if d_id not in existing_nodes:
            nodes.append({
                "id": d_id,
                "name": info['name'],
                "group": "drug",
                "toxicity": info['toxicity_score']
            })
            existing_nodes.add(d_id)

    return {"nodes": nodes, "links": links}


@app.get("/")
def health_check():
    return {"status": "Drug Optimizer API is running", "db": DB_PATH}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)