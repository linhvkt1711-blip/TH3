using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace TH3.Models
{
    public class PhoneModel
    {
        public int Id { get; set; }

        [Required, StringLength(100)]
        public string Name { get; set; } = string.Empty;

        [Required, StringLength(100)]
        public string Slug { get; set; } = string.Empty;

        [StringLength(20)]
        public string DeviceCode { get; set; } = "IP01"; // IP01, IP02, SS01

        [StringLength(50)]
        public string Brand { get; set; } = string.Empty;

        public string Model3DPath { get; set; } = string.Empty;

        public string AvailableColorsJson { get; set; } = "[]";

        // Danh sách mặc định để hệ thống luôn chạy mượt mà ngay cả khi chưa chạy migration database
        public static readonly List<PhoneModel> DefaultPhones = new List<PhoneModel>
        {
            new PhoneModel
            {
                Id = 1,
                Name = "iPhone 15 Pro",
                Slug = "iphone-15-pro",
                DeviceCode = "IP01",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-15-pro.glb",
                AvailableColorsJson = "[{\"name\":\"Titan Tự Nhiên\",\"hex\":\"#d0c4b4\"},{\"name\":\"Titan Xanh\",\"hex\":\"#2d3542\"},{\"name\":\"Titan Đen\",\"hex\":\"#3c3b3e\"},{\"name\":\"Titan Trắng\",\"hex\":\"#e2e4e1\"}]"
            },
            new PhoneModel
            {
                Id = 2,
                Name = "iPhone 15 Pro Max",
                Slug = "iphone-15-prm",
                DeviceCode = "IP02",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-15-prm.glb",
                AvailableColorsJson = "[{\"name\":\"Titan Tự Nhiên\",\"hex\":\"#d0c4b4\"},{\"name\":\"Titan Xanh\",\"hex\":\"#2d3542\"},{\"name\":\"Titan Đen\",\"hex\":\"#3c3b3e\"}]"
            },
            new PhoneModel
            {
                Id = 3,
                Name = "Samsung Galaxy S24 Ultra",
                Slug = "samsung-s24-ultra",
                DeviceCode = "SS01",
                Brand = "Samsung",
                Model3DPath = "/models/phones/samsung-s24-ultra.glb",
                AvailableColorsJson = "[{\"name\":\"Xám Titan\",\"hex\":\"#82807c\"},{\"name\":\"Đen Titan\",\"hex\":\"#262626\"},{\"name\":\"Tím Titan\",\"hex\":\"#483c50\"},{\"name\":\"Vàng Titan\",\"hex\":\"#f5e6c8\"}]"
            },
            new PhoneModel
            {
                Id = 4,
                Name = "iPhone 16 Pro Max",
                Slug = "iphone-16-pro-max",
                DeviceCode = "IP05",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-16-pro-max-no-sim-desert-titanium.glb",
                AvailableColorsJson = "[{\"name\":\"Titan Tự Nhiên\",\"hex\":\"#d0c4b4\"},{\"name\":\"Titan Xanh\",\"hex\":\"#2d3542\"},{\"name\":\"Titan Đen\",\"hex\":\"#3c3b3e\"},{\"name\":\"Titan Trắng\",\"hex\":\"#e2e4e1\"}]"
            },
            new PhoneModel
            {
                Id = 5,
                Name = "iPhone X",
                Slug = "iphone-x",
                DeviceCode = "IPX01",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-x/iphone_x.glb",
                AvailableColorsJson = "[{\"name\":\"Bạc (Silver)\",\"hex\":\"#f0f2f5\"},{\"name\":\"Xám không gian (Space Gray)\",\"hex\":\"#36383e\"}]"
            }
        };
    }
}
