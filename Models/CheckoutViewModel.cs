using TH3.Models;   // Nếu ShoppingCart và Order nằm cùng namespace thì không cần dòng này

namespace TH3.Models
{
    public class CheckoutViewModel
    {
        public ShoppingCart ShoppingCart { get; set; }
        public Order Order { get; set; }
        public string PaymentMethod { get; set; } = string.Empty;
        public string? QrCodeImage { get; set; }     // Base64 của QR
        public string? Instruction { get; set; }
    }
}