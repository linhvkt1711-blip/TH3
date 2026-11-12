using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using System.Security.Claims;
using TH3.Models;
using TH3.Services;

namespace TH3.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;

        private readonly IProductRepository _productRepository;

        private readonly ICategoryRepository _categoryRepository;

        private readonly RecommendationService _recommendationService;

        public HomeController(
            ILogger<HomeController> logger,
            IProductRepository productRepository,
            ICategoryRepository categoryRepository,
            RecommendationService recommendationService)
        {
            _logger = logger;

            _productRepository = productRepository;

            _categoryRepository = categoryRepository;

            _recommendationService = recommendationService;
        }

        public async Task<IActionResult> Index(
            string searchString,
            decimal? minPrice,
            decimal? maxPrice)
        {
            var productsQuery =
                await _productRepository.GetAllAsync();

            var products =
                productsQuery.AsQueryable();

            // SEARCH

            if (!string.IsNullOrEmpty(searchString))
            {
                searchString = searchString.Trim();

                var categories =
                    await _categoryRepository.GetAllAsync();

                var category =
                    categories.FirstOrDefault(c =>
                        c.Name.Equals(
                            searchString,
                            StringComparison.OrdinalIgnoreCase));

                if (category != null)
                {
                    products =
                        products.Where(p =>
                            p.CategoryId == category.Id);
                }
                else
                {
                    products =
                        products.Where(p =>
                            p.Name.Contains(
                                searchString,
                                StringComparison.OrdinalIgnoreCase));
                }

                ViewBag.SearchTerm = searchString;
            }

            // FILTER PRICE

            if (minPrice.HasValue)
            {
                products =
                    products.Where(p =>
                        p.Price >= minPrice.Value);
            }

            if (maxPrice.HasValue)
            {
                products =
                    products.Where(p =>
                        p.Price <= maxPrice.Value);
            }

            var productList = products.ToList();

            // AI RECOMMENDATION

            if (User.Identity != null &&
                User.Identity.IsAuthenticated)
            {
                var userId =
                    User.FindFirstValue(
                        ClaimTypes.NameIdentifier);

                var recommendations =
                    await _recommendationService
                    .GetRecommendations(userId ?? "");

                ViewBag.Recommendations =
                    recommendations;
            }

            ViewBag.SearchString =
                searchString ?? "";

            ViewBag.MinPrice =
                minPrice;

            ViewBag.MaxPrice =
                maxPrice;

            return View(productList);
        }

        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(
            Duration = 0,
            Location = ResponseCacheLocation.None,
            NoStore = true)]

        public IActionResult Error()
        {
            return View(
                new ErrorViewModel
                {
                    RequestId =
                        Activity.Current?.Id
                        ?? HttpContext.TraceIdentifier
                });
        }
    }
}