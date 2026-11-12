using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Authorization;
using Microsoft.EntityFrameworkCore;
using System.Security.Claims;
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Threading.Tasks;
using TH3.Models;

namespace TH3.Controllers
{
    public class ProductController : Controller
    {
        readonly IProductRepository _productRepository;

        readonly ICategoryRepository _categoryRepository;

        readonly IWebHostEnvironment _env;

        readonly ApplicationDbContext _context;

        public ProductController(
            IProductRepository productRepository,
            ICategoryRepository categoryRepository,
            IWebHostEnvironment env,
            ApplicationDbContext context)
        {
            _productRepository = productRepository;

            _categoryRepository = categoryRepository;

            _env = env;

            _context = context;
        }

        // =========================================================
        // INDEX
        // =========================================================

        public async Task<IActionResult> Index(
            string searchString,
            decimal? minPrice,
            decimal? maxPrice)
        {
            var products = await _productRepository.GetAllAsync();

            // SEARCH

            if (!string.IsNullOrEmpty(searchString))
            {
                products = products.Where(s =>
                    s.Name.Contains(
                        searchString,
                        StringComparison.OrdinalIgnoreCase)

                    ||

                    (s.Category != null &&
                     s.Category.Name.Contains(
                        searchString,
                        StringComparison.OrdinalIgnoreCase)));
            }

            // MIN PRICE

            if (minPrice.HasValue)
            {
                products =
                    products.Where(p =>
                        p.Price >= minPrice.Value);
            }

            // MAX PRICE

            if (maxPrice.HasValue)
            {
                products =
                    products.Where(p =>
                        p.Price <= maxPrice.Value);
            }

            ViewBag.SearchString = searchString ?? "";

            ViewBag.MinPrice = minPrice;

            ViewBag.MaxPrice = maxPrice;

            return View(products.ToList());
        }

        // =========================================================
        // ADD
        // =========================================================

        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Add()
        {
            var categories =
                await _categoryRepository.GetAllAsync();

            ViewBag.Categories =
                new SelectList(categories, "Id", "Name");

            return View();
        }

        [HttpPost]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Add(
            Product product,
            IFormFile ImageUrl,
            List<IFormFile> SubImages)
        {
            ModelState.Remove("ImageUrl");

            ModelState.Remove("ProductImages");

            if (ModelState.IsValid)
            {
                var uploadFolder =
                    Path.Combine(_env.WebRootPath, "images");

                if (!Directory.Exists(uploadFolder))
                {
                    Directory.CreateDirectory(uploadFolder);
                }

                // MAIN IMAGE

                if (ImageUrl != null)
                {
                    var fileName =
                        Guid.NewGuid().ToString()
                        + Path.GetExtension(ImageUrl.FileName);

                    using (var stream =
                        new FileStream(
                            Path.Combine(uploadFolder, fileName),
                            FileMode.Create))
                    {
                        await ImageUrl.CopyToAsync(stream);
                    }

                    product.ImageUrl =
                        "/images/" + fileName;
                }

                // SUB IMAGES

                if (SubImages != null &&
                    SubImages.Count > 0)
                {
                    product.ProductImages =
                        new List<ProductImage>();

                    foreach (var file in SubImages)
                    {
                        var subFileName =
                            Guid.NewGuid().ToString()
                            + Path.GetExtension(file.FileName);

                        using (var stream =
                            new FileStream(
                                Path.Combine(uploadFolder, subFileName),
                                FileMode.Create))
                        {
                            await file.CopyToAsync(stream);
                        }

                        product.ProductImages.Add(
                            new ProductImage
                            {
                                Url = "/images/" + subFileName
                            });
                    }
                }

                await _productRepository.AddAsync(product);

                return RedirectToAction(nameof(Index));
            }

            var categories =
                await _categoryRepository.GetAllAsync();

            ViewBag.Categories =
                new SelectList(categories, "Id", "Name");

            return View(product);
        }

        // =========================================================
        // DISPLAY
        // =========================================================

        public async Task<IActionResult> Display(int id)
        {
            Console.WriteLine("DISPLAY RUNNING");

            var product = await _productRepository.GetByIdAsync(id);

            if (product == null)
            {
                return NotFound();
            }

            var userId = User.Identity.IsAuthenticated
                ? User.FindFirstValue(ClaimTypes.NameIdentifier)
                : "GUEST_USER";

            _context.UserInteractionLogs.Add(
                new UserInteractionLog
                {
                    UserId = userId,
                    ProductId = product.Id,
                    Action = "View",
                    Timestamp = DateTime.Now
                });

            await _context.SaveChangesAsync();

            Console.WriteLine("LOG SAVED");

            var categories =
                await _categoryRepository.GetAllAsync();

            ViewBag.Categories =
                new SelectList(
                    categories,
                    "Id",
                    "Name",
                    product.CategoryId);

            return View(product);
        }

        // =========================================================
        // UPDATE
        // =========================================================

        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Update(int id)
        {
            var product =
                await _productRepository.GetByIdAsync(id);

            if (product == null)
            {
                return NotFound();
            }

            var categories =
                await _categoryRepository.GetAllAsync();

            ViewBag.Categories =
                new SelectList(
                    categories,
                    "Id",
                    "Name",
                    product.CategoryId);

            return View(product);
        }

        [HttpPost]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Update(
            int id,
            Product product,
            IFormFile ImageUrl,
            List<int> DeleteImageIds,
            List<IFormFile> NewSubImages)
        {
            if (id != product.Id)
            {
                return NotFound();
            }

            ModelState.Remove("ImageUrl");

            ModelState.Remove("ProductImages");

            if (ModelState.IsValid)
            {
                var existingProduct =
                    await _productRepository.GetByIdAsync(id);

                if (existingProduct == null)
                {
                    return NotFound();
                }

                var uploadFolder =
                    Path.Combine(_env.WebRootPath, "images");

                // DELETE SUB IMAGES

                if (DeleteImageIds != null &&
                    DeleteImageIds.Count > 0 &&
                    existingProduct.ProductImages != null)
                {
                    foreach (var imgId in DeleteImageIds)
                    {
                        var imgEntity =
                            existingProduct.ProductImages
                            .FirstOrDefault(i => i.Id == imgId);

                        if (imgEntity != null)
                        {
                            var fullPath =
                                Path.Combine(
                                    _env.WebRootPath,
                                    imgEntity.Url.TrimStart('/'));

                            if (System.IO.File.Exists(fullPath))
                            {
                                System.IO.File.Delete(fullPath);
                            }

                            existingProduct.ProductImages
                                .Remove(imgEntity);
                        }
                    }
                }

                // UPDATE MAIN IMAGE

                if (ImageUrl != null &&
                    ImageUrl.Length > 0)
                {
                    if (!string.IsNullOrEmpty(existingProduct.ImageUrl))
                    {
                        var oldImagePath =
                            Path.Combine(
                                _env.WebRootPath,
                                existingProduct.ImageUrl.TrimStart('/'));

                        if (System.IO.File.Exists(oldImagePath))
                        {
                            System.IO.File.Delete(oldImagePath);
                        }
                    }

                    var fileName =
                        Guid.NewGuid().ToString()
                        + Path.GetExtension(ImageUrl.FileName);

                    var filePath =
                        Path.Combine(uploadFolder, fileName);

                    using (var stream =
                        new FileStream(filePath, FileMode.Create))
                    {
                        await ImageUrl.CopyToAsync(stream);
                    }

                    existingProduct.ImageUrl =
                        "/images/" + fileName;
                }

                // ADD NEW SUB IMAGES

                if (NewSubImages != null &&
                    NewSubImages.Count > 0)
                {
                    if (existingProduct.ProductImages == null)
                    {
                        existingProduct.ProductImages =
                            new List<ProductImage>();
                    }

                    foreach (var file in
                        NewSubImages.Where(f => f.Length > 0))
                    {
                        var subFileName =
                            Guid.NewGuid().ToString()
                            + Path.GetExtension(file.FileName);

                        var subFilePath =
                            Path.Combine(uploadFolder, subFileName);

                        using (var stream =
                            new FileStream(subFilePath, FileMode.Create))
                        {
                            await file.CopyToAsync(stream);
                        }

                        existingProduct.ProductImages.Add(
                            new ProductImage
                            {
                                Url = "/images/" + subFileName
                            });
                    }
                }

                existingProduct.Name = product.Name;

                existingProduct.Price = product.Price;

                existingProduct.Description = product.Description;

                existingProduct.CategoryId = product.CategoryId;

                await _productRepository.UpdateAsync(existingProduct);

                return RedirectToAction(nameof(Index));
            }

            var categories =
                await _categoryRepository.GetAllAsync();

            ViewBag.Categories =
                new SelectList(
                    categories,
                    "Id",
                    "Name",
                    product.CategoryId);

            return View(product);
        }

        // =========================================================
        // TEST
        // =========================================================

        public IActionResult Test()
        {
            return Content("ProductController OK");
        }

        // =========================================================
        // DELETE
        // =========================================================

        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Delete(int id)
        {
            var product =
                await _productRepository.GetByIdAsync(id);

            if (product == null)
            {
                return NotFound();
            }

            return View(product);
        }

        [HttpPost, ActionName("Delete")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            await _productRepository.DeleteAsync(id);

            return RedirectToAction(nameof(Index));
        }
    }
}