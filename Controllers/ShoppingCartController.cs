using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using QRCoder;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using TH3.Extensions;
using TH3.Models;

namespace TH3.Controllers
{
    [Authorize]
    public class ShoppingCartController : Controller
    {
        private readonly ApplicationDbContext _context;
        private readonly UserManager<ApplicationUser> _userManager;
        private readonly IProductRepository _productRepository;

        public ShoppingCartController(
            ApplicationDbContext context,
            UserManager<ApplicationUser> userManager,
            IProductRepository productRepository)
        {
            _context = context;
            _userManager = userManager;
            _productRepository = productRepository;
        }

        // ====================== PHẦN THÊM VÀO GIỎ ======================

        // 1. Action cho nút "Thêm vào giỏ" - Bấm xong ở lại trang hiện tại
        [AllowAnonymous]
        public async Task<IActionResult> AddToCart(int productId, int quantity)
        {
            var product = await _productRepository.GetByIdAsync(productId);
            if (product == null) return NotFound();

            var cart = HttpContext.Session.GetObjectFromJson<ShoppingCart>("Cart") ?? new ShoppingCart();
            cart.AddItem(new CartItem
            {
                ProductId = productId,
                Name = product.Name,
                Price = product.Price,
                Quantity = quantity,
                ImageUrl = !string.IsNullOrEmpty(product.ImageUrl) ? product.ImageUrl : (product.ProductImages != null && product.ProductImages.Any() ? product.ProductImages.First().Url : "/images/no-image.png")
            });

            HttpContext.Session.SetObjectAsJson("Cart", cart);

            // Check if it's an AJAX request
            if (Request.Headers["X-Requested-With"] == "XMLHttpRequest")
            {
                int cartCount = cart.Items.Sum(i => i.Quantity);
                return Ok(new { success = true, message = "Sản phẩm đã được thêm vào giỏ hàng", cartCount = cartCount });
            }

            // Quay lại đúng trang người dùng vừa bấm nút
            string referer = Request.Headers["Referer"].ToString();
            if (!string.IsNullOrEmpty(referer))
            {
                return Redirect(referer);
            }
            return RedirectToAction("Index", "Home");
        }

        [AllowAnonymous]
        public async Task<IActionResult> BuyNow(int productId, int quantity)
        {
            var product = await _productRepository.GetByIdAsync(productId);
            if (product == null) return NotFound();

            var cart = HttpContext.Session.GetObjectFromJson<ShoppingCart>("Cart") ?? new ShoppingCart();
            cart.AddItem(new CartItem
            {
                ProductId = productId,
                Name = product.Name,
                Price = product.Price,
                Quantity = quantity,
                ImageUrl = !string.IsNullOrEmpty(product.ImageUrl) ? product.ImageUrl : (product.ProductImages != null && product.ProductImages.Any() ? product.ProductImages.First().Url : "/images/no-image.png")
            });

            HttpContext.Session.SetObjectAsJson("Cart", cart);

            // Bay thẳng sang trang Index của ShoppingCart
            return RedirectToAction("Index");
        }

        // ====================== PHẦN QUẢN LÝ GIỎ HÀNG ======================

        public IActionResult Index()
        {
            var cart = HttpContext.Session.GetObjectFromJson<ShoppingCart>("Cart") ?? new ShoppingCart();
            return View(cart);
        }

        [HttpPost]
        public IActionResult IncreaseQuantity(int productId)
        {
            var cart = HttpContext.Session.GetObjectFromJson<ShoppingCart>("Cart") ?? new ShoppingCart();
            var item = cart.Items.FirstOrDefault(i => i.ProductId == productId);
            if (item != null)
            {
                item.Quantity++;
                HttpContext.Session.SetObjectAsJson("Cart", cart);
            }
            return RedirectToAction("Index");
        }

        [HttpPost]
        public IActionResult DecreaseQuantity(int productId)
        {
            var cart = HttpContext.Session.GetObjectFromJson<ShoppingCart>("Cart") ?? new ShoppingCart();
            var item = cart.Items.FirstOrDefault(i => i.ProductId == productId);
            if (item != null)
            {
                item.Quantity--;
                if (item.Quantity <= 0)
                {
                    cart.RemoveItem(productId);
                }
                HttpContext.Session.SetObjectAsJson("Cart", cart);
            }
            return RedirectToAction("Index");
        }

        public IActionResult RemoveFromCart(int productId)
        {
            var cart = HttpContext.Session.GetObjectFromJson<ShoppingCart>("Cart");
            if (cart != null)
            {
                cart.RemoveItem(productId);
                HttpContext.Session.SetObjectAsJson("Cart", cart);
            }
            return RedirectToAction("Index");
        }

        // ====================== PHẦN THANH TOÁN (GIỮ NGUYÊN) ======================

        public IActionResult Checkout()
        {
            var cart = HttpContext.Session.GetObjectFromJson<ShoppingCart>("Cart");
            ViewBag.CartTotal = cart != null ? cart.Items.Sum(i => i.Price * i.Quantity) : 0;
            return View(new Order());
        }

        [HttpPost]
        public async Task<IActionResult> Checkout(Order order, string PaymentMethod)
        {
            var cart = HttpContext.Session.GetObjectFromJson<ShoppingCart>("Cart");
            if (cart == null || !cart.Items.Any())
            {
                return RedirectToAction("Index");
            }
            if (!ModelState.IsValid)
            {
                ViewBag.CartTotal = cart.Items.Sum(i => i.Price * i.Quantity);
                return View(order);
            }
            var user = await _userManager.GetUserAsync(User);

            if (user == null)
            {
                return Redirect("/Identity/Account/Login");
            }

            order.UserId = user.Id;
            order.ApplicationUserId = user.Id;
            order.OrderDate = DateTime.UtcNow;
            order.TotalPrice = cart.Items.Sum(i => i.Price * i.Quantity);
            order.PaymentMethod = PaymentMethod;
            order.PaymentStatus = "Pending";

            // Lưu chi tiết đơn hàng
            order.OrderDetails = cart.Items.Select(i => new OrderDetail
            {
                ProductId = i.ProductId,
                Quantity = i.Quantity,
                Price = i.Price
            }).ToList();

            if (string.IsNullOrEmpty(order.Notes))
            {
                order.Notes = ""; 
            }

            _context.Orders.Add(order);
            await _context.SaveChangesAsync();
            // Xử lý theo phương thức thanh toán
            switch (PaymentMethod)
            {
                case "COD":
                    HttpContext.Session.Remove("Cart");
                    TempData["Info"] = "Đơn hàng của bạn đã được đặt thành công và đang chờ duyệt bởi quản trị viên. Chúng tôi sẽ thông báo cho bạn khi đơn hàng được duyệt.";
                    return RedirectToAction("Index", "Order");

                case "MOMO":
                    await _context.SaveChangesAsync();
                    return RedirectToAction("MomoQR", new { orderId = order.Id });

                case "BANK":
                    await _context.SaveChangesAsync();
                    return RedirectToAction("BankQR", new { orderId = order.Id });

                default:
                    TempData["Error"] = "Vui lòng chọn phương thức thanh toán hợp lệ.";
                    return RedirectToAction("Checkout");
            }
        }

        public async Task<IActionResult> MomoQR(int orderId)
        {
            var order = await _context.Orders
                .Include(o => o.OrderDetails)
                .FirstOrDefaultAsync(o => o.Id == orderId);

            if (order == null) return NotFound();

            ViewBag.QrCodeBase64 = "/images/qr-momo-static.png";   // ← Bạn đặt file QR MoMo vào đây
            ViewBag.PaymentMethod = "Thanh toán MoMo";
            ViewBag.Instruction = "Mở ứng dụng MoMo → Quét mã QR để thanh toán";
            ViewBag.Order = order;

            return View("PaymentQR", order);   // Dùng chung view với BankQR
        }

        // ====================== HÀM TẠO VIETQR ======================
        public async Task<IActionResult> BankQR(int orderId)
        {
            var order = await _context.Orders
                .Include(o => o.OrderDetails)
                .FirstOrDefaultAsync(o => o.Id == orderId);

            if (order == null) return NotFound();

            ViewBag.QrCodeBase64 = "/images/qr-bank-static.png"; // QR Bank
            ViewBag.PaymentMethod = "Chuyển khoản ngân hàng";
            ViewBag.Instruction = "Mở app ngân hàng → Quét mã QR để chuyển khoản";
            ViewBag.Order = order;

            return View("PaymentQR", order);   // dùng chung view QR
        }

        // ====================== XÁC NHẬN ĐÃ CHUYỂN KHOẢN ======================
        public async Task<IActionResult> ConfirmPayment(int orderId)
        {
            var order = await _context.Orders.FindAsync(orderId);
            if (order == null)
            {
                TempData["Error"] = "Order not found!";
                return RedirectToAction("Index", "ShoppingCart");
            }

            // Update status
            order.PaymentStatus = "Paid";
            await _context.SaveChangesAsync();

            // Clear the shopping cart from session
            HttpContext.Session.Remove("Cart");

            // Optional: add a success message
            TempData["Success"] = $"Order #{orderId} has been marked as Paid.";

            // Redirect to OrderCompleted
            return RedirectToAction("OrderCompleted", new { id = orderId });
        }

        [HttpGet]
        public IActionResult OrderCompleted(int id)
        {
            // Optionally, you can load order details here if needed
            return View(id);
        }
        [Authorize(Roles = "Admin")]
        public IActionResult Revenue(DateTime? fromDate, DateTime? toDate)
        {
            var orders = _context.Orders
                .Where(o => o.PaymentStatus == "Paid")
                .ToList();

            var today = DateTime.Today;

            // 🔥 LUÔN TÍNH 4 Ô NÀY (KHÔNG PHỤ THUỘC FILTER)
            ViewBag.Today = orders
                .Where(o => o.OrderDate.Date == today)
                .Sum(o => o.TotalPrice);

            ViewBag.Week = orders
                .Where(o => o.OrderDate >= today.AddDays(-7))
                .Sum(o => o.TotalPrice);

            ViewBag.Month = orders
                .Where(o => o.OrderDate.Month == today.Month && o.OrderDate.Year == today.Year)
                .Sum(o => o.TotalPrice);

            ViewBag.Year = orders
                .Where(o => o.OrderDate.Year == today.Year)
                .Sum(o => o.TotalPrice);

            // 🔥 PHẦN LỌC (RIÊNG)
            var filteredOrders = orders.AsQueryable();

            if (fromDate.HasValue)
                filteredOrders = filteredOrders.Where(o => o.OrderDate >= fromDate.Value);

            if (toDate.HasValue)
                filteredOrders = filteredOrders.Where(o => o.OrderDate <= toDate.Value);

            var result = filteredOrders.ToList();

            ViewBag.TotalRevenue = result.Sum(o => o.TotalPrice);

            // 🔥 SẢN PHẨM (CÓ FILTER)
            var productStats = _context.OrderDetails
                .Include(od => od.Product)
                .Include(od => od.Order)
                .Where(od => od.Order.PaymentStatus == "Paid"
                    && (!fromDate.HasValue || od.Order.OrderDate >= fromDate.Value)
                    && (!toDate.HasValue || od.Order.OrderDate <= toDate.Value))
                .ToList()
                .GroupBy(od => od.Product.Name)
                .Select(g => new
                {
                    ProductName = g.Key,
                    TotalQuantity = g.Sum(x => x.Quantity),
                    TotalRevenue = g.Sum(x => x.Quantity * x.Price)
                })
                .ToList();

            ViewBag.ProductStats = productStats;

            return View();
        }
        public async Task<IActionResult> Details(int id)
        {
            var order = await _context.Orders
                .Include(o => o.OrderDetails)
                .ThenInclude(od => od.Product)
                .ThenInclude(p => p.ProductImages)
                .FirstOrDefaultAsync(o => o.Id == id);

            if (order == null)
            {
                return Content(" Không tìm thấy đơn hàng");
            }

            return View("~/Views/OrderManager/Details.cshtml", order);
        }
    }
}