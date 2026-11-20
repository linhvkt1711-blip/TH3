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
        public string DeviceCode { get; set; } = "IP01";

        [StringLength(50)]
        public string Brand { get; set; } = string.Empty;

        public string Model3DPath { get; set; } = string.Empty;

        public string AvailableColorsJson { get; set; } = "[]";

        // Danh sách các mẫu điện thoại có mô hình 3D
        public static readonly List<PhoneModel> DefaultPhones = new List<PhoneModel>
        {
            new PhoneModel
            {
                Id = 1,
                Name = "iPhone X / Xs (iPhone 10)",
                Slug = "iphone-x",
                DeviceCode = "IPX01",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-x/iphone_x.glb",
                AvailableColorsJson = "[{\"name\":\"Bạc (Silver)\",\"hex\":\"#f0f2f5\"},{\"name\":\"Xám không gian (Space Gray)\",\"hex\":\"#36383e\"},{\"name\":\"Vàng Gold\",\"hex\":\"#fad7bd\"}]"
            },
            new PhoneModel
            {
                Id = 3,
                Name = "iPhone 11",
                Slug = "iphone-11",
                DeviceCode = "IP11",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-11.glb",
                AvailableColorsJson = "[{\"name\":\"Đen\",\"hex\":\"#1f2020\"},{\"name\":\"Trắng\",\"hex\":\"#f9f6ef\"},{\"name\":\"Tím (Purple)\",\"hex\":\"#d1cdda\"},{\"name\":\"Xanh Mint\",\"hex\":\"#c7d8ca\"},{\"name\":\"Vàng\",\"hex\":\"#ffe681\"},{\"name\":\"Đỏ\",\"hex\":\"#ba0c2e\"}]"
            },
            new PhoneModel
            {
                Id = 4,
                Name = "iPhone 11 Pro Max",
                Slug = "iphone-11-prm",
                DeviceCode = "IP11PM",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-11-prm.glb",
                AvailableColorsJson = "[{\"name\":\"Đen\",\"hex\":\"#1f2020\"},{\"name\":\"Xám Space Gray\",\"hex\":\"#4c4a46\"},{\"name\":\"Bạc Silver\",\"hex\":\"#ebebe3\"},{\"name\":\"Vàng Gold\",\"hex\":\"#fad7bd\"}]"
            },
            new PhoneModel
            {
                Id = 5,
                Name = "iPhone 12",
                Slug = "iphone-12",
                DeviceCode = "IP12",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-12.glb",
                AvailableColorsJson = "[{\"name\":\"Xanh Navy\",\"hex\":\"#273444\"},{\"name\":\"Trắng\",\"hex\":\"#f9f6ef\"},{\"name\":\"Đen\",\"hex\":\"#1f2020\"},{\"name\":\"Xanh Lá\",\"hex\":\"#daf0db\"},{\"name\":\"Tím\",\"hex\":\"#b9b2db\"}]"
            },
            new PhoneModel
            {
                Id = 6,
                Name = "iPhone 12 Pro Max",
                Slug = "iphone-12-prm",
                DeviceCode = "IP12PM",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-12-prm.glb",
                AvailableColorsJson = "[{\"name\":\"Xanh Navy\",\"hex\":\"#273444\"},{\"name\":\"Trắng\",\"hex\":\"#f9f6ef\"},{\"name\":\"Đen\",\"hex\":\"#1f2020\"},{\"name\":\"Xanh Lá\",\"hex\":\"#daf0db\"},{\"name\":\"Tím\",\"hex\":\"#b9b2db\"}]"
            },
            new PhoneModel
            {
                Id = 7,
                Name = "iPhone 13",
                Slug = "iphone-13",
                DeviceCode = "IP13",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-13.glb",
                AvailableColorsJson = "[{\"name\":\"Xanh Midnight\",\"hex\":\"#1a2332\"},{\"name\":\"Ánh Sao Starlight\",\"hex\":\"#faf6f2\"},{\"name\":\"Hồng Pink\",\"hex\":\"#faddd7\"},{\"name\":\"Xanh Blue\",\"hex\":\"#215e7d\"},{\"name\":\"Xanh Green\",\"hex\":\"#394c38\"}]"
            },
            new PhoneModel
            {
                Id = 8,
                Name = "iPhone 13 Pro Max",
                Slug = "iphone-13-prm",
                DeviceCode = "IP13PM",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-13-prm.glb",
                AvailableColorsJson = "[{\"name\":\"Xanh Sierra Blue\",\"hex\":\"#9bb5ce\"},{\"name\":\"Xám Graphite\",\"hex\":\"#54524f\"},{\"name\":\"Vàng Gold\",\"hex\":\"#fae7cf\"},{\"name\":\"Bạc Silver\",\"hex\":\"#f1f2ed\"},{\"name\":\"Xanh Alpine Green\",\"hex\":\"#506152\"}]"
            },
            new PhoneModel
            {
                Id = 9,
                Name = "iPhone 14 Pro Max",
                Slug = "iphone-14-prm",
                DeviceCode = "IP14PM",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-14-prm.glb",
                AvailableColorsJson = "[{\"name\":\"Tím Deep Purple\",\"hex\":\"#594f63\"},{\"name\":\"Vàng Gold\",\"hex\":\"#f4e8ce\"},{\"name\":\"Bạc Silver\",\"hex\":\"#f0f2f2\"},{\"name\":\"Đen Space Black\",\"hex\":\"#3b3a3e\"}]"
            },
            new PhoneModel
            {
                Id = 10,
                Name = "iPhone 15 Pro",
                Slug = "iphone-15-pro",
                DeviceCode = "IP01",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-15-pro.glb",
                AvailableColorsJson = "[{\"name\":\"Titan Tự Nhiên\",\"hex\":\"#d0c4b4\"},{\"name\":\"Titan Xanh\",\"hex\":\"#2d3542\"},{\"name\":\"Titan Đen\",\"hex\":\"#3c3b3e\"},{\"name\":\"Titan Trắng\",\"hex\":\"#e2e4e1\"}]"
            },
            new PhoneModel
            {
                Id = 12,
                Name = "iPhone 16 Pro Max",
                Slug = "iphone-16-pro-max",
                DeviceCode = "IP05",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-16-pro-max-no-sim-desert-titanium.glb",
                AvailableColorsJson = "[{\"name\":\"Titan Sa Mạc\",\"hex\":\"#c5b098\"},{\"name\":\"Titan Tự Nhiên\",\"hex\":\"#d0c4b4\"},{\"name\":\"Titan Trắng\",\"hex\":\"#e2e4e1\"},{\"name\":\"Titan Đen\",\"hex\":\"#3c3b3e\"}]"
            },
            new PhoneModel
            {
                Id = 14,
                Name = "iPhone 18 Pro Max",
                Slug = "iphone-18-prm",
                DeviceCode = "IP18PM",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-18-prm.glb",
                AvailableColorsJson = "[{\"name\":\"Đỏ cherry\",\"hex\":\"#62100aff\"},{\"name\":\"Titan Tự Nhiên\",\"hex\":\"#d0c4b4\"},{\"name\":\"Titan Trắng\",\"hex\":\"#e2e4e1\"},{\"name\":\"Titan Đen\",\"hex\":\"#3c3b3e\"}]"
            },
            new PhoneModel
            {
                Id = 19,
                Name = "iPhone 17 Pro Max",
                Slug = "iphone-17-prm",
                DeviceCode = "IP17PM",
                Brand = "Apple",
                Model3DPath = "/models/phones/iphone-17-prm.glb",
                AvailableColorsJson = "[{\"name\":\"Silver\",\"hex\":\"#d5d5d2\"},{\"name\":\"Deep Blue\",\"hex\":\"#34475d\"},{\"name\":\"Cosmic Orange\",\"hex\":\"#d27648\"}]"
            },
        };
    }
}
