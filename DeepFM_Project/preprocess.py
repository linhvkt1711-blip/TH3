import pandas as pd
from sklearn.preprocessing import LabelEncoder
 
print("Loading dataset...")
 
events = pd.read_csv("dataset/events.csv")
 
print("Events loaded")
 
pos = events[events["event"] != "view"]          
neg = events[events["event"] == "view"].sample(   
    n=270000, random_state=42
)
 
events = pd.concat([pos, neg]).sample(frac=1, random_state=42).reset_index(drop=True)
 
print(f"Sau sampling: {len(events)} dòng — pos={len(pos)}, neg={len(neg)}")
 
prop1 = pd.read_csv("dataset/item_properties_part1.csv")
prop2 = pd.read_csv("dataset/item_properties_part2.csv")
properties = pd.concat([prop1, prop2])
 
print("Properties merged")
 
category_df = properties[
    properties["property"] == "categoryid"
][["itemid", "value"]]
category_df.columns = ["itemid", "categoryid"]
category_df = category_df.drop_duplicates("itemid")
 
print("Category extracted")
 
# Tạo label
events["label"] = events["event"].apply(
    lambda x: 0 if x == "view" else 1
)
 
# Merge
df = events.merge(category_df, on="itemid", how="left")
df["categoryid"] = df["categoryid"].fillna("unknown")
 
print("Merge completed")
 
# Encode
user_encoder     = LabelEncoder()
item_encoder     = LabelEncoder()
category_encoder = LabelEncoder()
 
df["user"]     = user_encoder.fit_transform(df["visitorid"])
df["item"]     = item_encoder.fit_transform(df["itemid"])
df["category"] = category_encoder.fit_transform(df["categoryid"])
 
print("Encoding completed")
 
final_df = df[["user", "item", "category", "label"]]
 
print(final_df["label"].value_counts())
print(f"Tỷ lệ label=1: {final_df['label'].mean()*100:.2f}%")
 
final_df.to_csv("processed_data.csv", index=False)
 
print("DONE")