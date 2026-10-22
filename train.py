import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

def train_model():
    with open("intents.json", "r") as file:
        dataset = json.load(file)

    corpus = []
    labels = []

    for intent in dataset["intents"]:
        for pattern in intent["patterns"]:
            corpus.append(pattern.lower())
            labels.append(intent["tag"])

    # TF-IDF and Logistic Regression Pipeline
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
        ("clf", LogisticRegression(max_iter=500, C=10.0))
    ])

    pipeline.fit(corpus, labels)
    joblib.dump(pipeline, "intent_model.joblib")
    print("Model training complete. Exported 'intent_model.joblib'.")

if __name__ == "__main__":
    train_model()