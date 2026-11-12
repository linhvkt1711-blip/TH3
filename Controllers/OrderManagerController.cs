using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace TH3.Controllers
{
    [Authorize(Roles = "Admin")]
    [Route("OrderManager")] // 👉 dùng OrderManager cho đúng URL
    public class OrderManagerController : Controller
    {
        private readonly ApplicationDbContext _context;

        public OrderManagerController(ApplicationDbContext context)
        {
            _context = context;
        }

        // ================= DANH SÁCH =================
        [HttpGet("")]
        public async Task<IActionResult> Index()
        {
            var orders = await _context.Orders
                .Include(o => o.ApplicationUser)
                .OrderByDescending(o => o.OrderDate)
                .ToListAsync();

            return View(orders);
        }

        // ================= DUYỆT ĐƠN =================
        [HttpPost("Approve")]
        public async Task<IActionResult> Approve(int id)
        {
            var order = await _context.Orders.FindAsync(id);

            if (order != null)
            {
                order.OrderStatus = "APPROVED";
                await _context.SaveChangesAsync();

                TempData["Success"] = $"Đã duyệt đơn hàng #{id} thành công!";
            }

            return RedirectToAction("Details", new { id = id });
        }

        // ================= TỪ CHỐI ĐƠN =================
        [HttpPost("Reject")]
        public async Task<IActionResult> Reject(int id, string rejectionReason = "")
        {
            var order = await _context.Orders.FindAsync(id);

            if (order != null)
            {
                order.OrderStatus = "REJECTED";
                order.Notes = string.IsNullOrEmpty(rejectionReason) 
                    ? order.Notes 
                    : (order.Notes ?? "") + $" [Lý do từ chối: {rejectionReason}]";
                
                await _context.SaveChangesAsync();

                TempData["Success"] = $"Đã từ chối đơn hàng #{id}!";
            }

            return RedirectToAction("Details", new { id = id });
        }

        // ================= CHI TIẾT =================
        [HttpGet("Details/{id}")]
        public async Task<IActionResult> Details(int id)
        {
            var order = await _context.Orders
                .Include(o => o.ApplicationUser)
                .Include(o => o.OrderDetails)
                .ThenInclude(od => od.Product)
                .ThenInclude(p => p.ProductImages)
                .FirstOrDefaultAsync(o => o.Id == id);

            if (order == null)
                return NotFound();

            return View(order);
        }
    }
}