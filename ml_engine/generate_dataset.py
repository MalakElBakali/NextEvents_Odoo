import random
import pandas as pd

CATEGORIES = {
    "corporate": [
        "Conférence d'entreprise",
        "Séminaire professionnel",
        "Réunion annuelle",
        "Team building",
    ],
    "social": [
        "Mariage",
        "Anniversaire",
        "Soirée privée",
        "Fête familiale",
    ],
    "cultural": [
        "Festival culturel",
        "Exposition artistique",
        "Concert de musique",
        "Spectacle de théâtre",
    ],
    "sport": [
        "Tournoi de football",
        "Match sportif",
        "Compétition régionale",
        "Course en plein air",
    ],
    "charity": [
        "Événement caritatif",
        "Collecte de dons",
        "Gala humanitaire",
        "Action associative",
    ],
}

rows = []

for category, titles in CATEGORIES.items():
    for _ in range(60):
        title = random.choice(titles)
        attendees = random.randint(20, 800)

        description = f"{title} avec environ {attendees} participants en plein air"
        duration = round(random.uniform(3, 7), 2)
        budget = attendees * random.randint(60, 130)
        staff = max(2, attendees // 30)

        rows.append({
            "description": description,
            "attendees": attendees,
            "category": category,
            "duration": duration,
            "budget": budget,
            "staff": staff,
        })

df = pd.DataFrame(rows)
df.to_csv("training_data.csv", index=False, encoding="utf-8")

print("✅ training_data.csv généré")
