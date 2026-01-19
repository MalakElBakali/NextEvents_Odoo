import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

# Charger données
df = pd.read_csv("training_data.csv")

X_text = df["description"]
y = df["category"]

# Vectorisation
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    stop_words=None,
    max_features=3000
)

X = vectorizer.fit_transform(X_text)

# Modèle simple et robuste
model = LogisticRegression(max_iter=1000)
model.fit(X, y)

# Sauvegarde
joblib.dump(model, "event_classifier.joblib")
joblib.dump(vectorizer, "tfidf_vectorizer.joblib")

print("✅ Modèle entraîné et sauvegardé")
