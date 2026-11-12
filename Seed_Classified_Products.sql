-- SCRIPT SEED DỮ LIỆU PHÂN LOẠI SẢN PHẨM: IP01, SS01, OL01, TN01...
-- Dành cho cơ sở dữ liệu QLBH (SQL Server)

USE [QLBH];
GO

-- 1. Đảm bảo danh mục "Ốp lưng" tồn tại
IF NOT EXISTS (SELECT 1 FROM Categories WHERE Name = N'Ốp lưng')
BEGIN
    INSERT INTO Categories (Name) 
    VALUES (N'Ốp lưng');
END
GO

DECLARE @CatePhone INT = (SELECT TOP 1 Id FROM Categories WHERE Name LIKE N'%Điện thoại%');
DECLARE @CateCase INT = (SELECT TOP 1 Id FROM Categories WHERE Name LIKE N'%Ốp%');
DECLARE @CateAudio INT = (SELECT TOP 1 Id FROM Categories WHERE Name LIKE N'%Âm thanh%' OR Name LIKE N'%Tai nghe%');
DECLARE @CateLaptop INT = (SELECT TOP 1 Id FROM Categories WHERE Name LIKE N'%Laptop%');

-- 2. Thêm Điện thoại mẫu chuẩn mã IP01, IP02, SS01
IF NOT EXISTS (SELECT 1 FROM Products WHERE Name LIKE N'%iPhone 15 Pro%')
BEGIN
    INSERT INTO Products (Name, Price, Description, ImageUrl, CategoryId)
    VALUES 
    (N'iPhone 15 Pro 128GB Titan Tự Nhiên (IP01)', 27990000, 
     N'Mã: IP01 | Flagship Apple khung viền Titan siêu nhẹ, chip A17 Pro mạnh mẽ, camera 48MP cao cấp.', 
     'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=500', @CatePhone),

    (N'iPhone 15 Pro Max 256GB Titan Tự Nhiên (IP02)', 33990000, 
     N'Mã: IP02 | Màn hình 6.7 inch Super Retina XDR, ống kính tiềm vọng Zoom quang học 5x.', 
     'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=500', @CatePhone),

    (N'Samsung Galaxy S24 Ultra 256GB Xám Titan (SS01)', 29990000, 
     N'Mã: SS01 | Quyền năng Galaxy AI, bút S-Pen tích hợp, khung viền Titan và camera mắt thần bóng đêm 200MP.', 
     'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=500', @CatePhone);
END

-- 3. Thêm Ốp lưng thời trang chuẩn mã OL01, OL02, OL03, OL04 (Có gắn mã thiết bị tương thích)
IF NOT EXISTS (SELECT 1 FROM Products WHERE Name LIKE N'%OL01%')
BEGIN
    INSERT INTO Products (Name, Price, Description, ImageUrl, CategoryId)
    VALUES 
    (N'Ốp Lưng iPhone 15 Pro MagSafe Trong Suốt Chống Ố (OL01)', 350000, 
     N'Mã: OL01 | Tương thích: iPhone 15 Pro (IP01)\nChất liệu TPU cao cấp trong suốt 100%, tích hợp vòng nam châm MagSafe hít cực mạnh, chống sốc 4 góc đạt chuẩn quân đội.', 
     'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500', @CateCase),

    (N'Ốp Lưng iPhone 15 Pro Da Bò Thuộc Cao Cấp Titan Gold (OL02)', 490000, 
     N'Mã: OL02 | Tương thích: iPhone 15 Pro (IP01)\nDa bò thật nguyên tấm nhập khẩu Ý, viền hợp kim nhôm gia công CNC bảo vệ ống kính camera, cảm giác cầm nắm êm ái sang trọng.', 
     'https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500', @CateCase),

    (N'Ốp Lưng iPhone 15 Pro Max Sợi Carbon Siêu Nhẹ (OL03)', 550000, 
     N'Mã: OL03 | Tương thích: iPhone 15 Pro Max (IP02)\nChế tác từ sợi Carbon 1500D siêu bền dùng trong hàng không vũ trụ, độ mỏng chỉ 0.6mm ôm sát thân máy nguyên bản.', 
     'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500', @CateCase),

    (N'Ốp Lưng Samsung S24 Ultra Giáp Chống Sốc UAG (OL04)', 620000, 
     N'Mã: OL04 | Tương thích: Samsung Galaxy S24 Ultra (SS01)\nThiết kế dạng tổ ong gia cường chống va đập từ độ cao 4.8 mét, gờ bảo vệ màn hình và cụm camera chuyên dụng.', 
     'https://images.unsplash.com/photo-1580910051074-3eb694886505?w=500', @CateCase);
END

-- 4. Thêm Tai nghe mã TN01, TN02
IF NOT EXISTS (SELECT 1 FROM Products WHERE Name LIKE N'%AirPods Pro%')
BEGIN
    INSERT INTO Products (Name, Price, Description, ImageUrl, CategoryId)
    VALUES 
    (N'Tai nghe Apple AirPods Pro 2 USB-C (TN01)', 5490000, 
     N'Mã: TN01 | Chống ồn chủ động ANC gấp 2 lần, âm thanh không gian cá nhân hóa, cổng sạc Type-C chuẩn mới.', 
     'https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=500', @CateAudio);
END

-- 5. Thêm Laptop mã LT01
IF NOT EXISTS (SELECT 1 FROM Products WHERE Name LIKE N'%MacBook Pro%')
BEGIN
    INSERT INTO Products (Name, Price, Description, ImageUrl, CategoryId)
    VALUES 
    (N'MacBook Pro 14 M3 Pro Space Black (LT01)', 49990000, 
     N'Mã: LT01 | Chip M3 Pro siêu mạnh, màn hình Liquid Retina XDR 120Hz, vỏ nhôm nguyên khối Space Black.', 
     'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500', @CateLaptop);
END
GO

PRINT N'Đã hoàn tất nạp dữ liệu phân loại sản phẩm chuẩn mã IP01, SS01, OL01, TN01!';
GO

