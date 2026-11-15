/* =========================================================================
   SCRIPT TẠO 10 MẪU ỐP LƯNG CHO 10 DÒNG IPHONE KHÁC NHAU
   Phân loại chính xác 100% bằng cột CompatibleDeviceCode:
   1.  iPhone X / Xs / 10 : IPX01
   2.  iPhone XR          : IPXR
   3.  iPhone 11          : IP11
   4.  iPhone 11 Pro Max  : IP11PM
   5.  iPhone 12          : IP12
   6.  iPhone 13          : IP13
   7.  iPhone 13 Pro Max  : IP13PM
   8.  iPhone 14 Pro Max  : IP14PM
   9.  iPhone 15 Pro      : IP01
   10. iPhone 16 Pro Max  : IP05
   ========================================================================= */

-- 1. Thêm các cột cần thiết vào bảng Products nếu chưa có
IF COL_LENGTH('dbo.Products', 'CompatibleDeviceCode') IS NULL
    ALTER TABLE dbo.Products ADD CompatibleDeviceCode nvarchar(20) NULL;

IF COL_LENGTH('dbo.Products', 'MaterialType') IS NULL
    ALTER TABLE dbo.Products ADD MaterialType nvarchar(40) NOT NULL CONSTRAINT DF_Products_MaterialType DEFAULT N'Silicone';

IF COL_LENGTH('dbo.Products', 'CaseTexturePath') IS NULL
    ALTER TABLE dbo.Products ADD CaseTexturePath nvarchar(500) NULL;

IF COL_LENGTH('dbo.Products', 'Case3DModelPath') IS NULL
    ALTER TABLE dbo.Products ADD Case3DModelPath nvarchar(500) NULL;
GO

-- 2. Đảm bảo danh mục "Ốp lưng" tồn tại
IF NOT EXISTS (SELECT 1 FROM Categories WHERE Name LIKE N'%Ốp%')
BEGIN
    INSERT INTO Categories (Name) VALUES (N'Ốp lưng');
END
GO

DECLARE @CaseCatId INT = (SELECT TOP 1 Id FROM Categories WHERE Name LIKE N'%Ốp%');

-- 3. XÓA CÁC MẪU CŨ CÙNG MÃ (ĐỂ TRÁNH TRÙNG LẶP KHI CHẠY LẠI)
DELETE FROM Products WHERE Name LIKE N'%OL_IP%';

-- 4. THÊM 10 MẪU ỐP CHO 10 DÒNG IPHONE KHÁC NHAU
-- 1. iPhone X / 10 (IPX01)
INSERT INTO Products (Name, Price, Description, ImageUrl, CaseTexturePath, MaterialType, CompatibleDeviceCode, CategoryId)
VALUES 
(N'Ốp Lưng iPhone X / 10 Trong Suốt Viền TPU Chống Ố (OL_IPX)', 
 180000, 
 N'Mã: OL_IPX | Tương thích: iPhone X / iPhone 10 (IPX01). Nhựa TPU dẻo cao cấp khoét cụm camera kép dọc chuẩn xác, mỏng nhẹ ôm sát thân máy.',
 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
 'Clear Silicone', 'IPX01', @CaseCatId);

-- 2. iPhone XR (IPXR)
INSERT INTO Products (Name, Price, Description, ImageUrl, CaseTexturePath, MaterialType, CompatibleDeviceCode, CategoryId)
VALUES 
(N'Ốp Lưng iPhone XR Liquid Silicone Màu Cam Coral (OL_IPXR)', 
 185000, 
 N'Mã: OL_IPXR | Tương thích: iPhone XR (IPXR). Silicone mịn màng khoét camera đơn chuẩn 100%, chống bám bẩn và chống sốc êm ái.',
 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500',
 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500',
 'Silicone', 'IPXR', @CaseCatId);

-- 3. iPhone 11 (IP11)
INSERT INTO Products (Name, Price, Description, ImageUrl, CaseTexturePath, MaterialType, CompatibleDeviceCode, CategoryId)
VALUES 
(N'Ốp Lưng iPhone 11 Trong Suốt Chống Trầy Góc Gia Cố (OL_IP11)', 
 190000, 
 N'Mã: OL_IP11 | Tương thích: iPhone 11 (IP11). Thiết kế khoét cụm 2 camera vuông chuẩn xác, 4 góc đệm khí chống va đập.',
 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
 'Clear Silicone', 'IP11', @CaseCatId);

-- 4. iPhone 11 Pro Max (IP11PM)
INSERT INTO Products (Name, Price, Description, ImageUrl, CaseTexturePath, MaterialType, CompatibleDeviceCode, CategoryId)
VALUES 
(N'Ốp Lưng iPhone 11 Pro Max Da Bò Thuộc Midnight Green (OL_IP11PM)', 
 260000, 
 N'Mã: OL_IP11PM | Tương thích: iPhone 11 Pro Max (IP11PM). Chất liệu da cao cấp màu xanh rêu sang trọng, viền gờ bảo vệ 3 camera lớn.',
 'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500',
 'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500',
 'Leather', 'IP11PM', @CaseCatId);

-- 5. iPhone 12 (IP12)
INSERT INTO Products (Name, Price, Description, ImageUrl, CaseTexturePath, MaterialType, CompatibleDeviceCode, CategoryId)
VALUES 
(N'Ốp Lưng iPhone 12 MagSafe Viền Vuông Phẳng Trong Suốt (OL_IP12)', 
 220000, 
 N'Mã: OL_IP12 | Tương thích: iPhone 12 (IP12). Thiết kế viền vuông phẳng đặc trưng iPhone 12, tích hợp vòng nam châm MagSafe hít từ tính mạnh mẽ.',
 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
 'Clear Silicone', 'IP12', @CaseCatId);

-- 6. iPhone 13 (IP13)
INSERT INTO Products (Name, Price, Description, ImageUrl, CaseTexturePath, MaterialType, CompatibleDeviceCode, CategoryId)
VALUES 
(N'Ốp Lưng iPhone 13 Silicone Màu Xanh Blue Khoét Camera Chéo (OL_IP13)', 
 230000, 
 N'Mã: OL_IP13 | Tương thích: iPhone 13 (IP13). Khoét chuẩn xác cụm 2 camera đặt chéo của iPhone 13, bề mặt phủ Nano mịn chống bám vân tay.',
 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500',
 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500',
 'Silicone', 'IP13', @CaseCatId);

-- 7. iPhone 13 Pro Max (IP13PM)
INSERT INTO Products (Name, Price, Description, ImageUrl, CaseTexturePath, MaterialType, CompatibleDeviceCode, CategoryId)
VALUES 
(N'Ốp Lưng iPhone 13 Pro Max Sợi Carbon Siêu Nhẹ Sierra Blue (OL_IP13PM)', 
 320000, 
 N'Mã: OL_IP13PM | Tương thích: iPhone 13 Pro Max (IP13PM). Vân sợi Carbon 1500D siêu bền mỏng 0.6mm, bảo vệ cụm 3 camera lồi kích thước lớn.',
 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500',
 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500',
 'Carbon', 'IP13PM', @CaseCatId);

-- 8. iPhone 14 Pro Max (IP14PM)
INSERT INTO Products (Name, Price, Description, ImageUrl, CaseTexturePath, MaterialType, CompatibleDeviceCode, CategoryId)
VALUES 
(N'Ốp Lưng iPhone 14 Pro Max MagSafe Deep Purple Sang Trọng (OL_IP14PM)', 
 350000, 
 N'Mã: OL_IP14PM | Tương thích: iPhone 14 Pro Max (IP14PM). Tone màu tím Deep Purple quý phái, viền bảo vệ cụm camera 48MP nhô cao.',
 'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500',
 'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500',
 'Leather', 'IP14PM', @CaseCatId);

-- 9. iPhone 15 Pro (IP01)
INSERT INTO Products (Name, Price, Description, ImageUrl, CaseTexturePath, MaterialType, CompatibleDeviceCode, CategoryId)
VALUES 
(N'Ốp Lưng iPhone 15 Pro MagSafe Trong Suốt Chống Ố Titan (OL_IP15P)', 
 360000, 
 N'Mã: OL_IP15P | Tương thích: iPhone 15 Pro (IP01). Khung TPU trong suốt 100% khoét nút Action Button, bảo vệ cụm 3 camera Titan lớn.',
 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
 'Clear Silicone', 'IP01', @CaseCatId);

-- 10. iPhone 16 Pro Max (IP05)
INSERT INTO Products (Name, Price, Description, ImageUrl, CaseTexturePath, MaterialType, CompatibleDeviceCode, CategoryId)
VALUES 
(N'Ốp Lưng iPhone 16 Pro Max MagSafe Titan Sa Mạc Armor (OL_IP16PM)', 
 490000, 
 N'Mã: OL_IP16PM | Tương thích: iPhone 16 Pro Max (IP05). Kích thước 6.9 inch lớn nhất Apple, khoét nút Camera Control sapphire độc quyền.',
 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
 'Silicone', 'IP05', @CaseCatId);
GO

-- 5. Cập nhật phân loại cho các sản phẩm ốp cũ nếu có
UPDATE Products SET CompatibleDeviceCode = 'IPX01'  WHERE (Name LIKE N'%iPhone X%' OR Name LIKE N'%iPhone 10%') AND (Name LIKE N'%Ốp%' OR Name LIKE N'%Case%');
UPDATE Products SET CompatibleDeviceCode = 'IPXR'   WHERE Name LIKE N'%iPhone XR%' AND (Name LIKE N'%Ốp%' OR Name LIKE N'%Case%');
UPDATE Products SET CompatibleDeviceCode = 'IP11'   WHERE Name LIKE N'%iPhone 11%' AND Name NOT LIKE N'%Pro%' AND (Name LIKE N'%Ốp%' OR Name LIKE N'%Case%');
UPDATE Products SET CompatibleDeviceCode = 'IP11PM' WHERE (Name LIKE N'%11 Pro Max%' OR Name LIKE N'%11 PRM%') AND (Name LIKE N'%Ốp%' OR Name LIKE N'%Case%');
UPDATE Products SET CompatibleDeviceCode = 'IP12'   WHERE Name LIKE N'%iPhone 12%' AND Name NOT LIKE N'%Pro%' AND (Name LIKE N'%Ốp%' OR Name LIKE N'%Case%');
UPDATE Products SET CompatibleDeviceCode = 'IP13'   WHERE Name LIKE N'%iPhone 13%' AND Name NOT LIKE N'%Pro%' AND (Name LIKE N'%Ốp%' OR Name LIKE N'%Case%');
UPDATE Products SET CompatibleDeviceCode = 'IP13PM' WHERE (Name LIKE N'%13 Pro Max%' OR Name LIKE N'%13 PRM%') AND (Name LIKE N'%Ốp%' OR Name LIKE N'%Case%');
UPDATE Products SET CompatibleDeviceCode = 'IP14PM' WHERE (Name LIKE N'%14 Pro Max%' OR Name LIKE N'%14 PRM%') AND (Name LIKE N'%Ốp%' OR Name LIKE N'%Case%');
UPDATE Products SET CompatibleDeviceCode = 'IP01'   WHERE Name LIKE N'%iPhone 15 Pro%' AND Name NOT LIKE N'%Max%' AND (Name LIKE N'%Ốp%' OR Name LIKE N'%Case%');
UPDATE Products SET CompatibleDeviceCode = 'IP05'   WHERE (Name LIKE N'%iPhone 16 Pro Max%' OR Name LIKE N'%16 PRM%') AND (Name LIKE N'%Ốp%' OR Name LIKE N'%Case%');
GO

PRINT N'✅ ĐÃ HOÀN TẤT TẠO 10 MẪU ỐP CHO 10 DÒNG IPHONE KHÁC NHAU VÀ PHÂN LOẠI CHUẨN XÁC!';
GO
