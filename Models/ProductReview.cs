using System.ComponentModel.DataAnnotations;
using TH3.Models;

namespace TH3.Models
{
    public class ProductReview
    {
        public int Id { get; set; }
        public int ProductId { get; set; }
        public string UserName { get; set; } // Tên người bình luận

        [Required(ErrorMessage = "Vui lòng nhập nội dung đánh giá")]
        public string Comment { get; set; }

        [Range(1, 5)]
        public int Rating { get; set; } // Số sao từ 1-5

        public DateTime CreatedDate { get; set; } = DateTime.Now;

        // Navigation property
        public Product? Product { get; set; }
    }
}