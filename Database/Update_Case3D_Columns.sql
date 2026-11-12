/* Chạy một lần trên database TH3 hiện tại trước khi chạy website. */
IF COL_LENGTH('dbo.Products', 'CompatibleDeviceCode') IS NULL
    ALTER TABLE dbo.Products ADD CompatibleDeviceCode nvarchar(20) NULL;

IF COL_LENGTH('dbo.Products', 'MaterialType') IS NULL
    ALTER TABLE dbo.Products ADD MaterialType nvarchar(40) NOT NULL CONSTRAINT DF_Products_MaterialType DEFAULT N'Silicone';

IF COL_LENGTH('dbo.Products', 'CaseTexturePath') IS NULL
    ALTER TABLE dbo.Products ADD CaseTexturePath nvarchar(500) NULL;

IF COL_LENGTH('dbo.Products', 'Case3DModelPath') IS NULL
    ALTER TABLE dbo.Products ADD Case3DModelPath nvarchar(500) NULL;

GO

-- Dùng ảnh chính hiện tại làm texture cho các sản phẩm có tên ốp/case.
UPDATE dbo.Products
SET CaseTexturePath = ImageUrl
WHERE CaseTexturePath IS NULL
  AND ImageUrl IS NOT NULL
  AND (Name LIKE N'%ốp%' OR Name LIKE N'%case%');
