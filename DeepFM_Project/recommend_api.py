from fastapi import FastAPI, HTTPException
import torch
import pandas as pd
from model import DeepFM

app = FastAPI()

print("Loading model...")

df = pd.read_csv("processed_data.csv")


user_encoder = {uid: idx for idx, uid in enumerate(df["user"].unique())}
item_encoder  = {iid: idx for idx, iid in enumerate(df["item"].unique())}

item_category_map = (
    df.drop_duplicates("item")
    .set_index("item")["category"]
    .to_dict()
)

model = DeepFM(
    num_users=df["user"].nunique(),
    num_items=df["item"].nunique(),
    num_categories=df["category"].nunique()
)
model.load_state_dict(torch.load("saved_model.pth"))
model.eval()

print("Model loaded")


@app.get("/recommend/{user_id}")
def recommend(user_id: int):

    
    encoded_user = user_encoder.get(user_id)
    if encoded_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    interacted = set(df[df["user"] == user_id]["item"].tolist())
    candidates = [i for i in df["item"].unique() if i not in interacted]


    encoded_items = [item_encoder[i] for i in candidates]
    categories    = [item_category_map.get(i, 0) for i in candidates]

  
    with torch.no_grad():
        scores = torch.sigmoid(model(
            torch.tensor([encoded_user] * len(encoded_items)),
            torch.tensor(encoded_items),
            torch.tensor(categories)
        )).squeeze().tolist()

    if isinstance(scores, float):
        scores = [scores]

    results = sorted(
        zip(candidates, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        {"item_id": int(item), "score": round(score, 4)}
        for item, score in results[:5]
    ]