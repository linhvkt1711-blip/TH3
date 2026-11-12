import torch
import pandas as pd
from model import DeepFM

print("Loading model...")
df = pd.read_csv("processed_data.csv")


user_encoder = {uid: idx for idx, uid in enumerate(df["user"].unique())}
item_encoder = {iid: idx for idx, iid in enumerate(df["item"].unique())}

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


raw_user_id = 10
user_id = user_encoder.get(raw_user_id)
if user_id is None:
    raise ValueError(f"User {raw_user_id} không tồn tại trong training data")


interacted_items = set(
    df[df["user"] == raw_user_id]["item"].tolist()
)
candidate_items = [
    item for item in df["item"].unique()
    if item not in interacted_items
]

print(f"Số item gợi ý: {len(candidate_items)}")


encoded_items = [item_encoder[i] for i in candidate_items]
categories    = [item_category_map.get(i, 0) for i in candidate_items]

user_tensor     = torch.tensor([user_id] * len(encoded_items))
item_tensor     = torch.tensor(encoded_items)
category_tensor = torch.tensor(categories)

print("Predicting...")
with torch.no_grad():
    scores = model(user_tensor, item_tensor, category_tensor)


scores = scores.squeeze().tolist()
if isinstance(scores, float):
    scores = [scores]

results = sorted(
    zip(candidate_items, scores),
    key=lambda x: x[1],
    reverse=True
)

print("\nTOP RECOMMENDATION\n")
for item, score in results[:10]:
    category = item_category_map.get(item, 0)
    print(f"Item: {item} | Category: {category} | Score: {score:.4f}")