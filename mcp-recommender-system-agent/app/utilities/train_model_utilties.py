import os
os.environ['WANDB_DISABLED'] = 'true'

from transformers import BertForSequenceClassification, Trainer, TrainingArguments
from transformers import BertTokenizer
import torch
import pandas as pd

# Custom Modules
from Config import TRAINING_MODEL_RESULTS_FOLDER, TRAINING_MODEL_LOGS_FOLDER

class RatingsDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        return {
            'input_ids': torch.tensor(self.encodings['input_ids'][idx]),
            'attention_mask': torch.tensor(self.encodings['attention_mask'][idx]),
            'labels': torch.tensor(self.labels[idx], dtype=torch.float)
        }

    def __len__(self):
        return len(self.labels)


# Create text input from available fields
def row_to_text(row):
    parts = []
    for col in [
        "Movie Name", "Year", "Timing(min)", "Genre", "Language",
        "Brief Description", "Cast", "Director", "Screenplay/Writer",
        "Production Company", "Budget in Rupees", "Revenue in Rupees",
        "User Liking (words)"
    ]:
        val = str(row[col]) if pd.notnull(row[col]) else ""
        parts.append(f"{col}: {val}")
    return " | ".join(parts)


def incremental_learning_the_model():
    pass

def train_movie_rating_model(data):
    df = data
    df["input_text"] = df.apply(row_to_text, axis=1)
    df["label"] = df["User Rating"].astype(float)
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    # Tokenize the dataset
    encodings = tokenizer(
        list(df["input_text"]),
        truncation=True,
        padding=True,
        max_length=512
    )
    dataset = RatingsDataset(encodings, df["label"].tolist())

    model = BertForSequenceClassification.from_pretrained(
        "bert-base-uncased",
        num_labels=1,  # Regression
        problem_type="regression"
    )

    training_args = TrainingArguments(
        output_dir=TRAINING_MODEL_RESULTS_FOLDER,
        num_train_epochs=10,
        per_device_train_batch_size=8,
        warmup_steps=10,
        weight_decay=0.01,
        logging_dir=TRAINING_MODEL_LOGS_FOLDER,
        logging_steps=10,
        save_strategy="no"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset
    )

    trainer.train()

    trainer.save_model(TRAINING_MODEL_RESULTS_FOLDER)
    tokenizer.save_pretrained(TRAINING_MODEL_RESULTS_FOLDER)

def predict_rating_of_movie(partial_input):
    # Load model and tokenizer
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    model = BertForSequenceClassification.from_pretrained(
        TRAINING_MODEL_RESULTS_FOLDER,  # or wherever you saved it
        num_labels=1,
        problem_type="regression"
    )
    model.eval()


    # Format partial input into text
    text = " | ".join(f"{k}: {v}" for k, v in partial_input.items() if v)
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    
    # Tokenize
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    
    # Predict
    with torch.no_grad():
        outputs = model(**inputs)
        prediction = outputs.logits.item()

    predicted_rating = prediction
    print(f"Predicted Rating: {predicted_rating:.2f}")
    return float(predicted_rating)


