using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Hosting;
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Threading.Tasks;
using TH3.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Authorization; // Quan trọng để dùng được .Include()
namespace TH3.Areas.Admin.Controllers
{
    [Area("Admin")]
    [Authorize(Roles = "Admin")]
    public class ProductController : Controller
    {
        readonly IProductRepository _productRepository;
        readonly ICategoryRepository _categoryRepository;
        readonly IWebHostEnvironment _env;

        public ProductController(IProductRepository productRepository, ICategoryRepository categoryRepository, IWebHostEnvironment env)
        {
            _productRepository = productRepository;
            _categoryRepository = categoryRepository;
            _env = env;
        }

        public async Task<IActionResult> Index()
        {
            var products = await _productRepository.GetAllAsync();
            return View(products);
        }

        public async Task<IActionResult> Add()
        {
            var categories = await _categoryRepository.GetAllAsync();
            ViewBag.Categories = new SelectList(categories, "Id", "Name");
            return View();
        }

        [HttpPost]
        public async Task<IActionResult> Add(Product product, IFormFile ImageUrl, List<IFormFile> SubImages)
        {
            ModelState.Remove("ImageUrl");
            ModelState.Remove("ProductImages");

            if (ModelState.IsValid)
            {
                var categoryList = await _categoryRepository.GetAllAsync();
                var selectedCategoryName = categoryList.FirstOrDefault(c => c.Id == product.CategoryId)?.Name ?? string.Empty;
                var isCaseProduct = selectedCategoryName.Contains("ốp", StringComparison.OrdinalIgnoreCase)
                    || selectedCategoryName.Contains("case", StringComparison.OrdinalIgnoreCase)
                    || product.Name.Contains("ốp", StringComparison.OrdinalIgnoreCase)
                    || product.Name.Contains("case", StringComparison.OrdinalIgnoreCase);

                var uploadFolder = Path.Combine(_env.WebRootPath, "images");
                if (!Directory.Exists(uploadFolder)) Directory.CreateDirectory(uploadFolder);

                if (ImageUrl != null && ImageUrl.Length > 0)
                {
                    var fileName = Guid.NewGuid().ToString() + Path.GetExtension(ImageUrl.FileName);
                    using (var stream = new FileStream(Path.Combine(uploadFolder, fileName), FileMode.Create))
                    {
                        await ImageUrl.CopyToAsync(stream);
                    }
                    product.ImageUrl = "/images/" + fileName;
                    // Ảnh chính của ốp được dùng làm texture mặt lưng trong Studio 3D.
                    if (isCaseProduct) product.CaseTexturePath = product.ImageUrl;
                }

                if (SubImages != null && SubImages.Count > 0)
                {
                    product.ProductImages = new List<ProductImage>();
                    foreach (var file in SubImages)
                    {
                        var subFileName = Guid.NewGuid().ToString() + Path.GetExtension(file.FileName);
                        using (var stream = new FileStream(Path.Combine(uploadFolder, subFileName), FileMode.Create))
                        {
                            await file.CopyToAsync(stream);
                        }
                        product.ProductImages.Add(new ProductImage { Url = "/images/" + subFileName });
                    }
                }

                product.MaterialType = string.IsNullOrWhiteSpace(product.MaterialType) ? "Silicone" : product.MaterialType;
                if (isCaseProduct && string.IsNullOrWhiteSpace(product.CaseTexturePath))
                    product.CaseTexturePath = product.ImageUrl;

                await _productRepository.AddAsync(product);
                return RedirectToAction(nameof(Index));
            }

            var categories = await _categoryRepository.GetAllAsync();
            ViewBag.Categories = new SelectList(categories, "Id", "Name");
            return View(product);
        }

        // Hàm Display dùng để hiển thị trang chi tiết sản phẩm
        public async Task<IActionResult> Display(int id)
        {
            var product = await _productRepository.GetByIdAsync(id);
            if (product == null) return NotFound();
            return View(product);
        }

        public async Task<IActionResult> Update(int id)
        {
            var product = await _productRepository.GetByIdAsync(id);
            if (product == null) return NotFound();

            var categories = await _categoryRepository.GetAllAsync();
            ViewBag.Categories = new SelectList(categories, "Id", "Name", product.CategoryId);
            return View(product);
        }

        [HttpPost]
        public async Task<IActionResult> Update(int id, Product product, IFormFile ImageUrl, List<int> DeleteImageIds, List<IFormFile> NewSubImages)
        {
            if (id != product.Id) return NotFound();

            ModelState.Remove("ImageUrl");
            ModelState.Remove("ProductImages");

            if (ModelState.IsValid)
            {
                var existingProduct = await _productRepository.GetByIdAsync(id);
                if (existingProduct == null) return NotFound();
                var categoryList = await _categoryRepository.GetAllAsync();
                var selectedCategoryName = categoryList.FirstOrDefault(c => c.Id == product.CategoryId)?.Name ?? string.Empty;
                var isCaseProduct = selectedCategoryName.Contains("ốp", StringComparison.OrdinalIgnoreCase)
                    || selectedCategoryName.Contains("case", StringComparison.OrdinalIgnoreCase)
                    || product.Name.Contains("ốp", StringComparison.OrdinalIgnoreCase)
                    || product.Name.Contains("case", StringComparison.OrdinalIgnoreCase);

                var uploadFolder = Path.Combine(_env.WebRootPath, "images");
                if (!Directory.Exists(uploadFolder)) Directory.CreateDirectory(uploadFolder);

                // 1. Xử lý xóa các ảnh phụ được đánh dấu
                if (DeleteImageIds != null && DeleteImageIds.Count > 0)
                {
                    foreach (var imgId in DeleteImageIds)
                    {
                        var imgEntity = existingProduct.ProductImages.FirstOrDefault(i => i.Id == imgId);
                        if (imgEntity != null)
                        {
                            var fullPath = Path.Combine(_env.WebRootPath, imgEntity.Url.TrimStart('/'));
                            if (System.IO.File.Exists(fullPath))
                            {
                                System.IO.File.Delete(fullPath);
                            }
                            existingProduct.ProductImages.Remove(imgEntity);
                        }
                    }
                }

                // 2. Cập nhật Ảnh chính mới
                if (ImageUrl != null)
                {
                    var fileName = Guid.NewGuid().ToString() + Path.GetExtension(ImageUrl.FileName);
                    using (var stream = new FileStream(Path.Combine(uploadFolder, fileName), FileMode.Create))
                    {
                        await ImageUrl.CopyToAsync(stream);
                    }
                    existingProduct.ImageUrl = "/images/" + fileName;
                    if (isCaseProduct) existingProduct.CaseTexturePath = existingProduct.ImageUrl;
                }

                // 3. Thêm các ảnh phụ mới
                if (NewSubImages != null && NewSubImages.Count > 0)
                {
                    if (existingProduct.ProductImages == null) existingProduct.ProductImages = new List<ProductImage>();

                    foreach (var file in NewSubImages)
                    {
                        var subFileName = Guid.NewGuid().ToString() + Path.GetExtension(file.FileName);
                        using (var stream = new FileStream(Path.Combine(uploadFolder, subFileName), FileMode.Create))
                        {
                            await file.CopyToAsync(stream);
                        }
                        existingProduct.ProductImages.Add(new ProductImage { Url = "/images/" + subFileName });
                    }
                }

                existingProduct.Name = product.Name;
                existingProduct.Price = product.Price;
                existingProduct.Description = product.Description;
                existingProduct.CategoryId = product.CategoryId;
                existingProduct.CompatibleDeviceCode = product.CompatibleDeviceCode;
                existingProduct.MaterialType = string.IsNullOrWhiteSpace(product.MaterialType) ? "Silicone" : product.MaterialType;
                if (isCaseProduct && !string.IsNullOrWhiteSpace(existingProduct.ImageUrl))
                    existingProduct.CaseTexturePath = existingProduct.ImageUrl;

                await _productRepository.UpdateAsync(existingProduct);
                return RedirectToAction(nameof(Index));
            }

            var categories = await _categoryRepository.GetAllAsync();
            ViewBag.Categories = new SelectList(categories, "Id", "Name", product.CategoryId);
            return View(product);
        }

        public async Task<IActionResult> Delete(int id)
        {
            var product = await _productRepository.GetByIdAsync(id);
            if (product == null) return NotFound();
            return View(product);
        }

        [HttpPost, ActionName("Delete")]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            await _productRepository.DeleteAsync(id);
            return RedirectToAction(nameof(Index));
        }
    }
}