using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Security.Claims;
using TH3.Models;

namespace TH3.Controllers
{
    [Authorize]
    [Route("MyOrder")]
    public class OrderController : Controller
    {
        private readonly ApplicationDbContext _context;

        public OrderController(ApplicationDbContext context)
        {
            _context = context;
        }

        // ================= DANH SÁCH ĐƠN USER =================
        [HttpGet("")]
        public async Task<IActionResult> Index()
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            bool isAdmin = User.IsInRole("Admin");

            var query = _context.Orders
                .Include(o => o.ApplicationUser)
                .Include(o => o.OrderDetails)
                .AsQueryable();

            if (!isAdmin)
            {
                query = query.Where(o => o.UserId == userId);
            }

            var orders = await query
                .OrderByDescending(o => o.OrderDate)
                .ToListAsync();

            return View(orders);
        }

        // ================= CHI TIẾT ĐƠN HÀNG =================
        [HttpGet("Details/{id}")]
        public async Task<IActionResult> Details(int id)
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            bool isAdmin = User.IsInRole("Admin");

            var query = _context.Orders
                .Where(o => o.Id == id)
                .Include(o => o.ApplicationUser)
                .Include(o => o.OrderDetails)
                    .ThenInclude(od => od.Product)
                        .ThenInclude(p => p.ProductImages)
                .AsQueryable();

            if (!isAdmin)
            {
                query = query.Where(o => o.UserId == userId);
            }

            var order = await query.FirstOrDefaultAsync();

            if (order == null)
            {
                // Nếu không tìm thấy đơn hàng hoặc đơn hàng không thuộc về User này
                return NotFound();
            }

            // Trả về View Details.cshtml (đảm bảo file nằm trong Views/Order/Details.cshtml)
            return View(order);
        }

        // ================= HỦY ĐƠN KHI KHÁCH HÀNG YÊU CẦU =================
        [HttpPost("Cancel/{id}")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Cancel(int id)
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var order = await _context.Orders.FirstOrDefaultAsync(o => o.Id == id && o.UserId == userId);

            if (order == null)
            {
                return NotFound();
            }

            if (order.OrderStatus != "PENDING_APPROVAL")
            {
                TempData["Info"] = "Đơn hàng chỉ có thể hủy khi đang chờ duyệt.";
                return RedirectToAction("Details", new { id });
            }

            order.OrderStatus = "CANCELLED";
            order.PaymentStatus = "Cancelled";
            await _context.SaveChangesAsync();

            TempData["Success"] = $"Đã hủy đơn hàng #{id} thành công.";
            return RedirectToAction("Index");
        }
    }
}