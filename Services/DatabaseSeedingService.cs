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
                // 1. Đảm bảo danh mục "Ốp lưng" tồn tại
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

                // 2. Kiểm tra nếu chưa có sản phẩm Ốp lưng chuẩn mã OL01, seed ngay 4 mẫu OL01, OL02, OL03, OL04
                bool hasCases = await _context.Products.AnyAsync(p => p.Name.Contains("OL01") || (p.CategoryId == caseCategory.Id && p.Name.Contains("MagSafe")));
                if (!hasCases)
                {
                    var sampleCases = new List<Product>
                    {
                        new Product
                        {
                            Name = "Ốp Lưng iPhone 15 Pro MagSafe Trong Suốt Chống Ố (OL01)",
                            Price = 350000,
                            Description = "Mã: OL01 | Tương thích: iPhone 15 Pro (IP01)\nChất liệu TPU cao cấp trong suốt 100%, tích hợp vòng nam châm MagSafe hít cực mạnh, chống sốc 4 góc đạt chuẩn quân đội.",
                            ImageUrl = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500",
                            CategoryId = caseCategory.Id
                        },
                        new Product
                        {
                            Name = "Ốp Lưng iPhone 15 Pro Da Bò Thuộc Cao Cấp Titan Gold (OL02)",
                            Price = 490000,
                            Description = "Mã: OL02 | Tương thích: iPhone 15 Pro (IP01)\nDa bò thật nguyên tấm nhập khẩu Ý, viền hợp kim nhôm gia công CNC bảo vệ ống kính camera, cảm giác cầm nắm êm ái sang trọng.",
                            ImageUrl = "https://images.unsplash.com/photo-1586105251261-72a756497a11?w=500",
                            CategoryId = caseCategory.Id
                        },
                        new Product
                        {
                            Name = "Ốp Lưng iPhone 15 Pro Max Sợi Carbon Siêu Nhẹ (OL03)",
                            Price = 550000,
                            Description = "Mã: OL03 | Tương thích: iPhone 15 Pro Max (IP02)\nChế tác từ sợi Carbon 1500D siêu bền dùng trong hàng không vũ trụ, độ mỏng chỉ 0.6mm ôm sát thân máy nguyên bản.",
                            ImageUrl = "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500",
                            CategoryId = caseCategory.Id
                        },
                        new Product
                        {
                            Name = "Ốp Lưng Samsung S24 Ultra Giáp Chống Sốc UAG (OL04)",
                            Price = 620000,
                            Description = "Mã: OL04 | Tương thích: Samsung Galaxy S24 Ultra (SS01)\nThiết kế dạng tổ ong gia cường chống va đập từ độ cao 4.8 mét, gờ bảo vệ màn hình và cụm camera chuyên dụng.",
                            ImageUrl = "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=500",
                            CategoryId = caseCategory.Id
                        }
                    };

                    _context.Products.AddRange(sampleCases);
                    await _context.SaveChangesAsync();
                }
            }
            catch (Exception ex)
            {
                // Bỏ qua lỗi nếu database chưa sẵn sàng để không làm gián đoạn ứng dụng
                Console.WriteLine($"Seeding warning: {ex.Message}");
            }
        }
    }
}
