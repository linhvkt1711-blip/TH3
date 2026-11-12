using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TH3.Models
{
    public class Product
    {
        public int Id { get; set; }

        [Required, StringLength(100)]
        public string Name { get; set; } = string.Empty;

        [Column(TypeName = "decimal(18, 2)")]
        public decimal Price { get; set; }

        public string Description { get; set; } = string.Empty;

        public string? ImageUrl { get; set; }

        public List<ProductImage>? ProductImages { get; set; }

        public int CategoryId { get; set; }

        public Category? Category { get; set; }

        // ================= PHÂN LOẠI MÃ SẢN PHẨM (IP01, SS01, OL01, TN01...) =================
        [NotMapped]
        private string? _productCode;

        [NotMapped]
        public string ProductCode
        {
            get
            {
                if (!string.IsNullOrEmpty(_productCode)) return _productCode;
                return AutoGenerateProductCode();
            }
            set => _productCode = value;
        }

        // Mã thiết bị tương thích: IP01, IP02, SS01... (được lưu trong SQL Server)
        [StringLength(20)]
        public string? CompatibleDeviceCode { get; set; }

        // Chất liệu ốp: Clear, Silicone, Leather, Hard...
        [StringLength(40)]
        public string MaterialType { get; set; } = "Silicone";

        // Ảnh sản phẩm dùng làm texture cho mô hình ốp 3D
        [StringLength(500)]
        public string? CaseTexturePath { get; set; }

        // Đường dẫn GLB tùy chọn nếu sau này có mô hình 3D thật
        [StringLength(500)]
        public string? Case3DModelPath { get; set; }

        private string AutoGenerateProductCode()
        {
            string nameUpper = (Name ?? string.Empty).ToUpper();
            string descUpper = (Description ?? string.Empty).ToUpper();
            string fullText = $"{nameUpper} {descUpper}";

            // 1. Kiểm tra xem tên hoặc mô tả có chứa mã chuẩn được gán sẵn không (OL01, IP01, SS01, TN01...)
            var match = System.Text.RegularExpressions.Regex.Match(fullText, @"\b(OL|IP|SS|TN|LT|TB)\d{2}\b");
            if (match.Success)
            {
                return match.Value;
            }

            string nameLower = (Name ?? string.Empty).ToLower();
            string cateLower = (Category?.Name ?? string.Empty).ToLower();

            // 2. Phân loại Ốp lưng: OL01, OL02, OL03...
            if (cateLower.Contains("ốp") || nameLower.Contains("ốp") || nameLower.Contains("case"))
            {
                int num = Id > 0 ? (Id % 90) + 1 : 1;
                return $"OL{num:D2}";
            }

            // 3. Phân loại Điện thoại iPhone: IP01, IP02...
            if (nameLower.Contains("iphone") || nameLower.Contains("apple"))
            {
                if (nameLower.Contains("15 pro max") || nameLower.Contains("15 prm")) return "IP02";
                if (nameLower.Contains("15 pro")) return "IP01";
                if (nameLower.Contains("16 pro max") || nameLower.Contains("16 prm")) return "IP05";
                if (nameLower.Contains("16 pro")) return "IP06";
                if (nameLower.Contains("16")) return "IP07";
                if (nameLower.Contains("15")) return "IP03";
                if (nameLower.Contains("14")) return "IP04";
                int num = Id > 0 ? (Id % 90) + 1 : 1;
                return $"IP{num:D2}";
            }

            // 4. Phân loại Điện thoại Samsung: SS01, SS02...
            if (nameLower.Contains("samsung") || nameLower.Contains("galaxy"))
            {
                if (nameLower.Contains("s24 ultra")) return "SS01";
                if (nameLower.Contains("s24")) return "SS02";
                if (nameLower.Contains("s23")) return "SS03";
                if (nameLower.Contains("z fold") || nameLower.Contains("fold")) return "SS04";
                int num = Id > 0 ? (Id % 90) + 1 : 1;
                return $"SS{num:D2}";
            }

            // 5. Phân loại Tai nghe / Âm thanh: TN01, TN02...
            if (cateLower.Contains("âm thanh") || cateLower.Contains("tai nghe") || nameLower.Contains("airpods") || nameLower.Contains("tai nghe") || nameLower.Contains("buds") || nameLower.Contains("headphone"))
            {
                int num = Id > 0 ? (Id % 90) + 1 : 1;
                return $"TN{num:D2}";
            }

            // 6. Phân loại Laptop: LT01, LT02...
            if (cateLower.Contains("laptop") || nameLower.Contains("laptop") || nameLower.Contains("macbook") || nameLower.Contains("dell") || nameLower.Contains("asus"))
            {
                int num = Id > 0 ? (Id % 90) + 1 : 1;
                return $"LT{num:D2}";
            }

            // 7. Phân loại Máy tính bảng: TB01, TB02...
            if (cateLower.Contains("máy tính bảng") || cateLower.Contains("tablet") || nameLower.Contains("ipad") || nameLower.Contains("tab"))
            {
                int num = Id > 0 ? (Id % 90) + 1 : 1;
                return $"TB{num:D2}";
            }

            // Mặc định
            return $"SP{Math.Max(1, Id):D2}";
        }
    }
}
