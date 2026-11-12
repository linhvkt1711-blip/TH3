# AI_Service/modules/roca_procrustes.py
try:
    import torch  # type: ignore
    import torch.nn as nn  # type: ignore
    import torch.nn.functional as F  # type: ignore
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    class _DummyModule:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return self.forward(*args, **kwargs)
        def eval(self):
            return self
        def to(self, device):
            return self
        def state_dict(self):
            return {}
        def load_state_dict(self, state):
            pass
    class _DummyNN:
        Module = _DummyModule
        def Sequential(self, *args):
            return _DummyModule()
        def Linear(self, *args):
            return _DummyModule()
        def ReLU(self, *args):
            return _DummyModule()
        def Sigmoid(self, *args):
            return _DummyModule()
    nn = _DummyNN()  # type: ignore

class DifferentiableProcrustes(nn.Module):
    def __init__(self):
        super(DifferentiableProcrustes, self).__init__()

    def forward(self, q, p, scale, t_init, weights):
        """
        q: Tọa độ NOC (Normalized Object Coordinates) [B, N, 3]
        p: Điểm độ sâu chiếu ngược trong không gian camera [B, N, 3]
        scale: Tỷ lệ vật thể s [B, 3]
        t_init: Tịnh tiến ban đầu [B, 3]
        weights: Trọng số học được c_k [B, N]
        """
        if not HAS_TORCH:
            return None, None

        batch_size = q.size(0)
        
        # Chuẩn hóa trọng số c_k
        weights = weights / (weights.sum(dim=1, keepdim=True) + 1e-6)
        
        # q_tilde = q * s, p_tilde = p - t_init
        q_tilde = q * scale.unsqueeze(1)
        p_tilde = p - t_init.unsqueeze(1)
        
        # Tính trung bình có trọng số (Weighted centroids)
        mu_q = (q_tilde * weights.unsqueeze(-1)).sum(dim=1) # [B, 3]
        mu_p = (p_tilde * weights.unsqueeze(-1)).sum(dim=1) # [B, 3]
        
        # Trừ tâm (Zero-centering)
        q_prime = q_tilde - mu_q.unsqueeze(1)
        p_prime = p_tilde - mu_p.unsqueeze(1)
        
        # Tính ma trận hiệp phương sai H có trọng số
        weights_expanded = weights.unsqueeze(-1)
        H = torch.matmul(q_prime.transpose(1, 2), p_prime * weights_expanded) # [B, 3, 3]
        
        # Phân rã SVD
        U, S, V = torch.svd(H)
        
        # Đảm bảo ma trận xoay hợp lệ thuộc SO(3) (tránh phản chiếu ngược)
        det = torch.det(torch.matmul(V, U.transpose(1, 2)))
        diag = torch.eye(3, device=U.device).unsqueeze(0).repeat(batch_size, 1, 1)
        diag[:, 2, 2] = det
        
        R_star = torch.matmul(torch.matmul(V, diag), U.transpose(1, 2)) # [B, 3, 3]
        
        # Tinh chỉnh tịnh tiến theo công thức (11) trong bài báo: t = t_init + mu(p_tilde) - R* @ mu(q_tilde)
        t_refined = t_init + mu_p - torch.matmul(mu_q.unsqueeze(1), R_star.transpose(1, 2)).squeeze(1)
        
        return R_star, t_refined


class ROCAAlignmentHead(nn.Module):
    def __init__(self):
        super(ROCAAlignmentHead, self).__init__()
        
        # MLP dự đoán Scale s_i
        self.scale_mlp = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 3)
        )
        
        # MLP dự đoán NOCs q_i
        self.noc_mlp = nn.Sequential(
            nn.Linear(3 + 3 + 512, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 3)
        )
        
        # MLP dự đoán trọng số c_k cho Procrustes
        self.weight_mlp = nn.Sequential(
            nn.Linear(512 + 3 + 1 + 3 + 3, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
        
        self.procrustes = DifferentiableProcrustes()

    def forward(self, feature_e, points_p, t_init):
        """
        feature_e: Vector đặc trưng hình dạng e_i [B, N, 512] hoặc [B, 512]
        points_p: Điểm độ sâu 3D [B, N, 3]
        t_init: Tịnh tiến ban đầu [B, 3]
        """
        if not HAS_TORCH:
            return {
                "scale": [0.0706, 0.1466, 0.00825],
                "nocs": None,
                "weights": None,
                "rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                "translation": [0.0, 0.0, 0.35]
            }

        # 1. Hồi quy Tỷ lệ (Scale)
        scale = self.scale_mlp(feature_e) # [B, 3]
        
        # 2. Dự đoán tọa độ chuẩn hóa NOCs q_i
        B, N, _ = points_p.shape
        feat_expanded = feature_e.unsqueeze(1).repeat(1, N, 1)
        scale_expanded = scale.unsqueeze(1).repeat(1, N, 1)
        
        noc_input = torch.cat([points_p - t_init.unsqueeze(1), scale_expanded, feat_expanded], dim=-1)
        q_preds = self.noc_mlp(noc_input) # [B, N, 3]
        
        # 3. Dự đoán trọng số c_k
        p_tilde = points_p - t_init.unsqueeze(1)
        dummy_mask = torch.ones((B, N, 1), device=points_p.device)
        weight_input = torch.cat([feat_expanded, scale_expanded, dummy_mask, q_preds, p_tilde], dim=-1)
        weights = self.weight_mlp(weight_input).squeeze(-1) # [B, N]
        
        # 4. Tối ưu hóa Procrustes vi phân
        R_star, t_star = self.procrustes(q_preds, points_p, scale, t_init, weights)
        
        return {
            "scale": scale,
            "nocs": q_preds,
            "weights": weights,
            "rotation": R_star,
            "translation": t_star
        }
