import torch
import torch.nn as nn
 
 
class DeepFM(nn.Module):
 
    def __init__(
        self,
        num_users,
        num_items,
        num_categories,
        embed_dim=16
    ):
 
        super(DeepFM, self).__init__()
 
        # Embedding
        self.user_embedding = nn.Embedding(num_users, embed_dim)
        self.item_embedding = nn.Embedding(num_items, embed_dim)
        self.category_embedding = nn.Embedding(num_categories, embed_dim)
 
        # Bias
        self.user_bias = nn.Embedding(num_users, 1)
        self.item_bias = nn.Embedding(num_items, 1)
        self.category_bias = nn.Embedding(num_categories, 1)
 
        # Deep Neural Network
        self.deep = nn.Sequential(
            nn.Linear(embed_dim * 3, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
 
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
 
            nn.Linear(64, 1)
        )
 
    # 0.5 * sum_k [ (Σ_i V_ik)² - Σ_i (V_ik)² ]
    def fm_part(self, user_emb, item_emb, category_emb):
        stacked = torch.stack(
            [user_emb, item_emb, category_emb],
            dim=1
        )  

        # (Σ_i V_i)² — tổng theo chiều field rồi bình phương
        sum_square = stacked.sum(dim=1) ** 2   

        # Σ_i (V_i²) — bình phương từng field rồi tổng lại
        square_sum = (stacked ** 2).sum(dim=1) 

        # Tổng theo chiều embed_dim → ra 1 scalar mỗi sample
        fm = 0.5 * (sum_square - square_sum).sum(dim=1, keepdim=True)
    

        return fm
 
 
    def forward(self, user, item, category):
 
        user_emb = self.user_embedding(user)
        item_emb = self.item_embedding(item)
        category_emb = self.category_embedding(category)
 
        # FM
        fm_output = self.fm_part(user_emb, item_emb, category_emb)
 
        # Linear
        linear = (
            self.user_bias(user) +
            self.item_bias(item) +
            self.category_bias(category)
        )
 

        deep_input = torch.cat([
            user_emb, item_emb, category_emb
        ], dim=1)
 
        deep_output = self.deep(deep_input)
 
  
        output = linear + fm_output + deep_output
 
        return output
 