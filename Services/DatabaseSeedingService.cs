using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using TH3.Models;

namespace TH3.Services
{
    public class DatabaseSeedingService
    {
        private readonly ApplicationDbContext _context;

        public DatabaseSeedingService(ApplicationDbContext context)
        {
            _context = context;
        }

        public async Task SeedClassifiedProductsAsync()
        {
            try
            {
                // 1. Đảm bảo database đã áp dụng migration
                await _context.Database.MigrateAsync();

                // 2. Đảm bảo danh mục "Ốp lưng" tồn tại
                var caseCategory = await _context.Categories
                    .FirstOrDefaultAsync(c => c.Name.Contains("Ốp") || c.Name.Contains("Case"));

                if (caseCategory == null)
                {
                    caseCategory = new Category
                    {
                        Name = "Ốp lưng"
                    };
                    _context.Categories.Add(caseCategory);
                    await _context.SaveChangesAsync();
                }

                // 3. Danh sách 10 mẫu ốp lưng chuẩn riêng biệt cho 10 dòng iPhone
                var tenIPhoneCases = new List<Product>
                {
                    new Product
                    {
                        Name = "Ốp Lưng iPhone X / 10 Trong Suốt Viền TPU Chống Ố (OL_IPX)",
                        Price = 180000,
                        Description = "Mã: OL_IPX | Tương thích: iPhone X / iPhone 10 (IPX01). Nhựa TPU dẻo cao cấp khoét cụm camera kép dọc chuẩn xác, mỏng nhẹ ôm sát thân máy.",
                        ImageUrl = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                        CaseTexturePath = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                        MaterialType = "Clear Silicone",
                        CompatibleDeviceCode = "IPX01",
                        CategoryId = caseCategory.Id
                    },
                    new Product
                    {
                        Name = "Ốp Lưng iPhone 11 Trong Suốt Chống Trầy Góc Gia Cố (OL_IP11)",
                        Price = 190000,
                        Description = "Mã: OL_IP11 | Tương thích: iPhone 11 (IP11). Thiết kế khoét cụm 2 camera vuông chuẩn xác, 4 góc đệm khí chống va đập.",
                        ImageUrl = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                        CaseTexturePath = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                        MaterialType = "Clear Silicone",
                        CompatibleDeviceCode = "IP11",
                        CategoryId = caseCategory.Id
                    },
                    new Product
                    {
                        Name = "Ốp Lưng iPhone 11 Pro Max Da Bò Thuộc Midnight Green (OL_IP11PM)",
                        Price = 260000,
                        Description = "Mã: OL_IP11PM | Tương thích: iPhone 11 Pro Max (IP11PM). Chất liệu da cao cấp màu xanh rêu sang trọng, viền gờ bảo vệ 3 camera lớn.",
                        ImageUrl = "https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500",
                        CaseTexturePath = "https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500",
                        MaterialType = "Leather",
                        CompatibleDeviceCode = "IP11PM",
                        CategoryId = caseCategory.Id
                    },
                    new Product
                    {
                        Name = "Ốp Lưng iPhone 12 MagSafe Viền Vuông Phẳng Trong Suốt (OL_IP12)",
                        Price = 220000,
                        Description = "Mã: OL_IP12 | Tương thích: iPhone 12 (IP12). Thiết kế viền vuông phẳng đặc trưng iPhone 12, tích hợp vòng nam châm MagSafe hít từ tính mạnh mẽ.",
                        ImageUrl = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                        CaseTexturePath = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                        MaterialType = "Clear Silicone",
                        CompatibleDeviceCode = "IP12",
                        CategoryId = caseCategory.Id
                    },
                    new Product
                    {
                        Name = "Ốp Lưng iPhone 13 Silicone Màu Xanh Blue Khoét Camera Chéo (OL_IP13)",
                        Price = 230000,
                        Description = "Mã: OL_IP13 | Tương thích: iPhone 13 (IP13). Khoét chuẩn xác cụm 2 camera đặt chéo của iPhone 13, bề mặt phủ Nano mịn chống bám vân tay.",
                        ImageUrl = "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500",
                        CaseTexturePath = "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500",
                        MaterialType = "Silicone",
                        CompatibleDeviceCode = "IP13",
                        CategoryId = caseCategory.Id
                    },
                    new Product
                    {
                        Name = "Ốp Lưng iPhone 13 Pro Max Sợi Carbon Siêu Nhẹ Sierra Blue (OL_IP13PM)",
                        Price = 320000,
                        Description = "Mã: OL_IP13PM | Tương thích: iPhone 13 Pro Max (IP13PM). Vân sợi Carbon 1500D siêu bền mỏng 0.6mm, bảo vệ cụm 3 camera lồi kích thước lớn.",
                        ImageUrl = "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500",
                        CaseTexturePath = "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500",
                        MaterialType = "Carbon",
                        CompatibleDeviceCode = "IP13PM",
                        CategoryId = caseCategory.Id
                    },
                    new Product
                    {
                        Name = "Ốp Lưng iPhone 14 Pro Max MagSafe Deep Purple Sang Trọng (OL_IP14PM)",
                        Price = 350000,
                        Description = "Mã: OL_IP14PM | Tương thích: iPhone 14 Pro Max (IP14PM). Tone màu tím Deep Purple quý phái, viền bảo vệ cụm camera 48MP nhô cao.",
                        ImageUrl = "https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500",
                        CaseTexturePath = "https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500",
                        MaterialType = "Leather",
                        CompatibleDeviceCode = "IP14PM",
                        CategoryId = caseCategory.Id
                    },
                    new Product
                    {
                        Name = "Ốp Lưng iPhone 15 Pro MagSafe Trong Suốt Chống Ố Titan (OL_IP15P)",
                        Price = 360000,
                        Description = "Mã: OL_IP15P | Tương thích: iPhone 15 Pro (IP01). Khung TPU trong suốt 100% khoét nút Action Button, bảo vệ cụm 3 camera Titan lớn.",
                        ImageUrl = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                        CaseTexturePath = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                        MaterialType = "Clear Silicone",
                        CompatibleDeviceCode = "IP01",
                        CategoryId = caseCategory.Id
                    },
                    new Product
                    {
                        Name = "Ốp Lưng iPhone 16 Pro Max MagSafe Titan Sa Mạc Armor (OL_IP16PM)",
                        Price = 490000,
                        Description = "Mã: OL_IP16PM | Tương thích: iPhone 16 Pro Max (IP05). Kích thước 6.9 inch lớn nhất Apple, khoét nút Camera Control sapphire độc quyền.",
                        ImageUrl = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                        CaseTexturePath = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                        MaterialType = "Silicone",
                        CompatibleDeviceCode = "IP05",
                        CategoryId = caseCategory.Id
                    }
                };

                foreach (var sampleCase in tenIPhoneCases)
                {
                    bool exists = await _context.Products.AnyAsync(p => p.Name == sampleCase.Name || (p.CompatibleDeviceCode == sampleCase.CompatibleDeviceCode && p.Name.Contains(sampleCase.CompatibleDeviceCode)));
                    if (!exists)
                    {
                        _context.Products.Add(sampleCase);
                    }
                }

                await _context.SaveChangesAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Seeding warning: {ex.Message}");
            }
        }
    }
}
