import joblib

model = joblib.load("event_classifier.joblib")
vectorizer = joblib.load("tfidf_vectorizer.joblib")

text = "Conférence d'entreprise en plein air avec 300 participants"
X = vectorizer.transform([text])

pred = model.predict(X)[0]

if hasattr(model, "predict_proba"):
    confidence = max(model.predict_proba(X)[0])
else:
    confidence = 0.0

print("Catégorie :", pred)
print("Confiance :", round(confidence, 2))
