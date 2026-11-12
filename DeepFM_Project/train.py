import pandas as pd
import torch
 
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
 
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, log_loss
 
from model import DeepFM
 
print("Loading processed data...")
 
df = pd.read_csv("processed_data.csv")
 
X = df[["user", "item", "category"]]
y = df["label"]
 
# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
 
print("Train test split completed")
 
 
# Dataset class
class RecDataset(Dataset):
 
    def __init__(self, X, y):
 
        self.users = torch.tensor(
            X["user"].values, dtype=torch.long
        )
        self.items = torch.tensor(
            X["item"].values, dtype=torch.long
        )
        self.categories = torch.tensor(
            X["category"].values, dtype=torch.long
        )
        self.labels = torch.tensor(
            y.values, dtype=torch.float32
        )
 
    def __len__(self):
        return len(self.labels)
 
    def __getitem__(self, idx):
        return (
            self.users[idx],
            self.items[idx],
            self.categories[idx],
            self.labels[idx]
        )
 
 
train_dataset = RecDataset(X_train, y_train)
 
train_loader = DataLoader(
    train_dataset, batch_size=1024, shuffle=True
)
 
test_loader = DataLoader(
    RecDataset(X_test, y_test), batch_size=1024
)
 
print("Creating model...")
 
model = DeepFM(
    num_users=df["user"].nunique(),
    num_items=df["item"].nunique(),
    num_categories=df["category"].nunique()
)
 
pos_weight = torch.tensor([75.0 / 25.0])
 
criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
 
optimizer = torch.optim.Adam(
    model.parameters(), lr=0.001
)
 
epochs = 100
 
# Early stopping
best_auc = 0
best_logloss = float("inf")
patience = 5
no_improve = 0
 
print("Start training...")
print(f"{'Epoch':>6} | {'Train Loss':>12} | {'Val Logloss':>12} | {'Val AUC':>10}")
print("-" * 50)
 
for epoch in range(epochs):
 
    # ── TRAIN ──
    model.train()
    total_loss = 0
 
    for users, items, categories, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(users, items, categories).squeeze()
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    train_logloss = total_loss / len(train_loader)
 
    model.eval()
    all_preds = []
    all_labels = []
 
    with torch.no_grad():
        for users, items, categories, labels in test_loader:
            preds = torch.sigmoid(
                model(users, items, categories)
            ).squeeze()
            all_preds.extend(preds.tolist())
            all_labels.extend(labels.tolist())
 
    val_auc = roc_auc_score(all_labels, all_preds)
    # log_loss của sklearn = Logloss chuẩn (trung bình theo từng sample)
    val_logloss = log_loss(all_labels, all_preds)
 
    print(f"{epoch+1:>6} | {train_logloss:>12.4f} | {val_logloss:>12.4f} | {val_auc:>10.4f}")
 
    # ── EARLY STOPPING: theo dõi val AUC ──
    if val_auc > best_auc:
        best_auc = val_auc
        best_logloss = val_logloss
        no_improve = 0
        torch.save(model.state_dict(), "saved_model.pth")  # lưu model tốt nhất
    else:
        no_improve += 1
        if no_improve >= patience:
            print(f"\nEarly stopping tại epoch {epoch+1} — không cải thiện sau {patience} epoch liên tiếp.")
            break
 
print("\nMODEL SAVED (best checkpoint)")
print(f"\n{'='*50}")
print(f"Kết quả tốt nhất:")
print(f"  Val AUC     : {best_auc:.4f}")
print(f"  Val Logloss : {best_logloss:.4f}")
print(f"{'='*50}")
 
if best_auc >= 0.80:
    print("=> Tốt!")
elif best_auc >= 0.75:
    print("=> Khá!")
elif best_auc >= 0.60:
    print("=> Trung bình, cần train thêm")
else:
    print("=> Chưa tốt, kiểm tra lại data")