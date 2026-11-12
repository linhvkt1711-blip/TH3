using Microsoft.AspNetCore.Mvc.ModelBinding.Validation;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TH3.Models
{
    public class Order
    {
        public int Id { get; set; }

        [ValidateNever]
        public string UserId { get; set; } = string.Empty;
       
        public DateTime OrderDate { get; set; }

        [Column(TypeName = "decimal(18,2)")]
        public decimal TotalPrice { get; set; }

        [Required(ErrorMessage = "Vui lòng nhập địa chỉ giao hàng")]
        public string ShippingAddress { get; set; } = string.Empty;

        public string? Notes { get; set; }
        
        public string? ApplicationUserId { get; set; }
        
        public string PaymentMethod { get; set; } = string.Empty;

        public string PaymentStatus { get; set; } = "Pending";

        public string OrderStatus { get; set; } = "PENDING_APPROVAL";

        [ForeignKey("UserId")]
        [ValidateNever]
        public ApplicationUser? ApplicationUser { get; set; }

        public List<OrderDetail> OrderDetails { get; set; } = new List<OrderDetail>();

        public Order()
        {
            PaymentStatus = "Pending";
            OrderStatus = "PENDING_APPROVAL";
        }
    }
}