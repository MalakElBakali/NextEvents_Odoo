# -*- coding: utf-8 -*-
"""
NextEvents - ML Engine (Flask)
- /health : vérifier que le service répond
- /predict : prédire catégorie + estimations
Le service fonctionne même sans modèle (fallback mock).
"""

import os
import re
from typing import Any, Dict, Tuple

from flask import Flask, jsonify, request

# joblib est utilisé pour charger les modèles (quand ils existent)
try:
    import joblib
except Exception:
    joblib = None


app = Flask(__name__)

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
MODEL_PATH = os.getenv("MODEL_PATH", "/app/event_classifier.joblib")
VECTORIZER_PATH = os.getenv("VECTORIZER_PATH", "/app/tfidf_vectorizer.joblib")

# Si USE_MOCK=1 -> on force le mode mock même si les fichiers existent
USE_MOCK = os.getenv("USE_MOCK", "0") == "1"

# Objets chargés en mémoire (si dispo)
classifier = None
vectorizer = None


# -------------------------------------------------------------------
# Utilitaires : nettoyage + heuristiques d'estimation
# -------------------------------------------------------------------
def clean_text(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def estimate_duration_budget_staff(category: str, attendees: int) -> Tuple[float, float, int]:
    """
    Heuristiques simples mais cohérentes :
    - duration (heures)
    - budget (MAD)
    - staff (personnes)
    Ces formules sont volontairement "défendables" et stables.
    """
    attendees = max(0, int(attendees or 0))

    # Base par catégorie
    base = {
        "corporate": {"duration": 3.0, "budget": 800.0, "staff": 4},
        "social":    {"duration": 5.0, "budget": 600.0, "staff": 5},
        "cultural":  {"duration": 4.0, "budget": 700.0, "staff": 6},
        "sport":     {"duration": 6.0, "budget": 500.0, "staff": 7},
        "charity":   {"duration": 4.0, "budget": 400.0, "staff": 6},
    }.get(category, {"duration": 4.0, "budget": 600.0, "staff": 5})

    # Ajustements en fonction du volume
    # - Durée augmente doucement avec l'ampleur
    duration = base["duration"] + min(6.0, attendees / 200.0)

    # - Budget : coût par participant dépend du type + coût fixe
    #   (valeurs volontairement raisonnables, tu pourras les calibrer avec ton dataset)
    cost_per_attendee = {
        "corporate": 120.0,
        "social":    90.0,
        "cultural":  100.0,
        "sport":     80.0,
        "charity":   60.0,
    }.get(category, 90.0)

    budget = base["budget"] * 100 + (cost_per_attendee * attendees)  # base*100 pour avoir des MAD réalistes

    # - Staff : ratio simple (1 staff / 30 pers) + base
    staff = base["staff"] + (attendees // 30)

    # Arrondis propres
    duration = round(float(duration), 2)
    budget = round(float(budget), 2)
    staff = int(staff)

    return duration, budget, staff


def safe_confidence(proba: Any) -> float:
    """
    proba peut venir de predict_proba : array shape (1, n_classes)
    """
    try:
        p = float(max(proba[0]))
        return max(0.0, min(1.0, p))
    except Exception:
        return 0.0


# -------------------------------------------------------------------
# Chargement modèle
# -------------------------------------------------------------------
def load_model_if_available() -> Dict[str, Any]:
    """
    Charge classifier + vectorizer si fichiers présents et joblib dispo.
    Retourne un dict d'état exploitable par /health.
    """
    global classifier, vectorizer

    status = {
        "joblib_available": joblib is not None,
        "model_file_exists": os.path.exists(MODEL_PATH),
        "vectorizer_file_exists": os.path.exists(VECTORIZER_PATH),
        "loaded": False,
        "mode": "mock" if USE_MOCK else "auto",
    }

    if USE_MOCK:
        return status

    if joblib is None:
        return status

    if not (os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH)):
        return status

    try:
        classifier = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        status["loaded"] = True
        status["mode"] = "model"
    except Exception:
        # On laisse loaded=False et on retombe en mock
        pass

    return status


MODEL_STATUS = load_model_if_available()


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.get("/health")
def health():
    """
    Healthcheck pour Docker + debug rapide.
    """
    # refresh léger (utile si tu montes des volumes et ajoutes les joblib après)
    global MODEL_STATUS
    MODEL_STATUS = load_model_if_available()

    return jsonify({
        "status": "ok",
        "service": "nextevents_ml_engine",
        "mode": MODEL_STATUS.get("mode", "mock"),
        "model_loaded": MODEL_STATUS.get("loaded", False),
    })


@app.post("/predict")
def predict():
    """
    Input:
      {
        "description": "...",
        "attendees": 120
      }

    Output:
      {
        "category": "corporate",
        "confidence": 0.82,
        "duration": 3.5,
        "budget": 25000,
        "staff": 8
      }
    """
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        try:
            payload = request.get_json(force=True)
        except Exception:
            payload = {}

    if not payload and request.data:
        try:
            import json
            payload = json.loads(request.data.decode("utf-8", errors="ignore"))
        except Exception:
            payload = {}


    print("==== DEBUG REQUEST ====")
    print("RAW DATA :", request.data)
    print("JSON PAYLOAD :", payload)

    description = clean_text(payload.get("description", ""))
    attendees = payload.get("attendees", 0)

    print("DESCRIPTION CLEAN :", description)
    print("DESCRIPTION LENGTH :", len(description))
    print("ATTENDEES :", attendees)
    print("=======================")

    if not description or len(description) < 5:
        return jsonify({"error": "description too short"}), 400

    # refresh léger à chaque appel (pratique en dev)
    global MODEL_STATUS
    MODEL_STATUS = load_model_if_available()

    # --- Mode modèle si dispo ---
    if MODEL_STATUS.get("loaded") and classifier is not None and vectorizer is not None:
        try:
            X = vectorizer.transform([description])
            pred = classifier.predict(X)[0]

            confidence = 0.0
            if hasattr(classifier, "predict_proba"):
                proba = classifier.predict_proba(X)
                confidence = safe_confidence(proba)

            # Estimations (heuristiques pour l’instant)
            duration, budget, staff = estimate_duration_budget_staff(pred, attendees)

            return jsonify({
                "category": pred,
                "confidence": confidence,
                "duration": duration,
                "budget": budget,
                "staff": staff
            })
        except Exception:
            # fallback mock en cas de souci de modèle
            pass

    # --- Mode mock (fallback) ---
    # petite logique "keyword" pour rendre le mock intelligent
    keywords = {
        "corporate": ["conférence", "séminaire", "team building", "entreprise", "réunion", "business"],
        "social":    ["mariage", "anniversaire", "fête", "soirée", "baptême"],
        "cultural":  ["festival", "concert", "exposition", "théâtre", "culture"],
        "sport":     ["tournoi", "match", "course", "sport", "compétition"],
        "charity":   ["caritatif", "don", "collecte", "humanitaire", "association"],
    }

    category = "social"
    for cat, words in keywords.items():
        if any(w in description for w in words):
            category = cat
            break

    duration, budget, staff = estimate_duration_budget_staff(category, attendees)

    return jsonify({
        "category": category,
        "confidence": 0.55,
        "duration": duration,
        "budget": budget,
        "staff": staff
    })


if __name__ == "__main__":
    # Important: host=0.0.0.0 pour Docker
    app.run(host="0.0.0.0", port=5000, debug=True)
