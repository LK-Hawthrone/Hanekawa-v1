import random
import time
import json
import os

# =========================
# Paths & Data Loading
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

QA_TEMPLATES = load_json("qa_templates.json")
FLAVOURS = load_json("flavours.json")
TRAITS = load_json("traits.json")
FALLBACKS = load_json("fallbacks.json")

# =========================
# Mood Configuration
# =========================

MOOD_MIN = -100
MOOD_MAX = 100
MOOD_TARGET = 20  # natural equilibrium

# =========================
# Intents
# =========================

INTENTS = {
    "greeting": ["hi", "hello", "hey"],
    "sadness": ["sad", "tired", "down", "bad"],
    "happiness": ["happy", "good", "great"],
    "sleep": ["sleep", "bed", "night"],
    "name_call": ["hanekawa"]
}

# =========================
# Text Utilities
# =========================

def normalize_text(text):
    return text.lower().strip()

def tokenize(text):
    return normalize_text(text).split()

# =========================
# Intent Detection
# =========================

def detect_intent(tokens):
    scores = {}

    for intent, keywords in INTENTS.items():
        score = sum(1 for t in tokens if t in keywords)
        if score:
            scores[intent] = score

    return max(scores, key=scores.get) if scores else "unknown"

# =========================
# Candidate Selection
# =========================

def get_candidates(intent):
    return [
        qa for qa in QA_TEMPLATES
        if qa["intent"] == intent or qa["intent"] == "any"
    ]

# =========================
# Utility Scoring
# =========================

def compute_utility(qa, intent, state):
    score = 0
    mood = state["mood"]

    if qa["intent"] == intent:
        score += 50
    elif qa["intent"] == "any":
        score += 10
    else:
        return -999

    cond = qa.get("conditions", {})

    if "mood_min" in cond and mood < cond["mood_min"]:
        return -999
    if "mood_max" in cond and mood > cond["mood_max"]:
        return -999

    if qa["id"] == state["last_qa_id"]:
        score -= 15

    return score

# =========================
# Candidate Choice
# =========================

def choose_best(candidates, intent, state):
    scored = []

    for qa in candidates:
        s = compute_utility(qa, intent, state)
        if s > -999:
            scored.append((s, qa))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0], reverse=True)
    return random.choice(scored[:3])[1]

# =========================
# Mood Zones
# =========================

def mood_zone(mood):
    if mood <= -50:
        return "angry"
    if mood <= -10:
        return "lazy"
    if mood >= 50:
        return "playful"
    return "neutral"

# =========================
# Trait & Flavour
# =========================

def pick_trait(state):
    zone = mood_zone(state["mood"])
    pool = TRAITS.get(zone, TRAITS["neutral"])
    return random.choice(pool) if random.random() < 0.35 else None

def pick_flavour():
    lines = []

    if random.random() < FLAVOURS["comments"]["chance"]:
        lines.append(random.choice(FLAVOURS["comments"]["lines"]))

    if random.random() < 0.2:
        lines.append(random.choice(FLAVOURS["actions"]))

    return lines

# =========================
# Mood Homeostasis
# =========================

def apply_homeostasis(state):
    mood = state["mood"]

    if mood < MOOD_TARGET:
        mood += 2
    elif mood > MOOD_TARGET:
        mood -= 1

    state["mood"] = max(MOOD_MIN, min(MOOD_MAX, mood))

# =========================
# Output Builder (ROBUST)
# =========================

def build_output(qa, state):
    output = []

    # Response (safe)
    responses = qa.get("response")
    if isinstance(responses, list) and responses:
        output.append(random.choice(responses))

    # Question (safe)
    questions = qa.get("question")
    if isinstance(questions, list) and questions:
        output.append(random.choice(questions))

    # Trait
    trait = pick_trait(state)
    if trait:
        output.append(trait)

    # Flavour
    output.extend(pick_flavour())

    # Absolute safety net
    if not output:
        return random.choice(FALLBACKS["generic"])

    return " ".join(output)

# =========================
# Main Processing
# =========================

def process_input(user_input, state):
    now = time.time()

    # ---- Ensure state keys ----
    state.setdefault("mood", MOOD_TARGET)
    state.setdefault("last_qa_id", None)
    state.setdefault("repeat_name_count", 0)
    state.setdefault("session", {"turn": 0, "last_input_time": now})

    # ---- Timing ----
    idle = int(now - state["session"]["last_input_time"])
    state["session"]["last_input_time"] = now
    state["session"]["turn"] += 1

    tokens = tokenize(user_input)
    intent = detect_intent(tokens)

    # ---- Name spam penalty ----
    if "hanekawa" in tokens:
        state["repeat_name_count"] += 1
        if state["repeat_name_count"] >= 3:
            state["mood"] -= 3
    else:
        state["repeat_name_count"] = 0

    # ---- Unknown intent is mild friction ----
    if intent == "unknown":
        state["mood"] -= 1

    candidates = get_candidates(intent)
    selected = choose_best(candidates, intent, state)

    if not selected:
        apply_homeostasis(state)
        return random.choice(FALLBACKS["confused"]), False

    # ---- Mood delta ----
    delta = int(selected.get("mood_delta", 0))
    delta = max(-9, min(9, delta))
    state["mood"] += delta

    apply_homeostasis(state)

    state["last_qa_id"] = selected["id"]

    response = build_output(selected, state)

    return response, bool(selected.get("exit"))

# Entry point 
if __name__ == "__main__": 
    start_cli()