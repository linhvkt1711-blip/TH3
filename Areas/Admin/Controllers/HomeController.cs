using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using TH3.Models;

namespace TH3.Areas.Admin.Controllers
{
    [Area("Admin")]
    [Authorize(Roles = SD.Role_Admin)]
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;
        private readonly IProductRepository _productRepository;
        private readonly ICategoryRepository _categoryRepository;

        public HomeController(ILogger<HomeController> logger, IProductRepository productRepository, ICategoryRepository categoryRepository)
        {
            _logger = logger;
            _productRepository = productRepository;
            _categoryRepository = categoryRepository;
        }

        public async Task<IActionResult> Index(string searchString)
        {
            // 1. Lấy toàn bộ sản phẩm kèm theo thông tin Category để lọc chính xác
            var productsQuery = await _productRepository.GetAllAsync();
            var products = productsQuery.AsQueryable();

            if (!string.IsNullOrEmpty(searchString))
            {
                searchString = searchString.Trim(); // Xóa khoảng trắng thừa

                // 2. Lấy danh sách danh mục để kiểm tra
                var categories = await _categoryRepository.GetAllAsync();

                // Tìm danh mục có tên khớp với searchString (không phân biệt hoa thường)
                var category = categories.FirstOrDefault(c => c.Name.Equals(searchString, StringComparison.OrdinalIgnoreCase));

                if (category != null)
                {
                    // Nếu là danh mục, lọc theo CategoryId
                    products = products.Where(p => p.CategoryId == category.Id);
                }
                else
                {
                    // Nếu không phải danh mục, tìm theo tên sản phẩm
                    products = products.Where(p => p.Name.Contains(searchString, StringComparison.OrdinalIgnoreCase));
                }

                ViewBag.SearchTerm = searchString;
            }

            return View(products.ToList());
        }

        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}