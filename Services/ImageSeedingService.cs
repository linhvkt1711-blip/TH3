using TH3.Models;
using Microsoft.EntityFrameworkCore;

namespace TH3.Services
{
    public class ImageSeedingService
    {
        private readonly ApplicationDbContext _context;

        public ImageSeedingService(ApplicationDbContext context)
        {
            _context = context;
        }

        /// <summary>
        /// Adds multiple images to a product
        /// </summary>
        public async Task AddImagesToProductAsync(int productId, List<string> imageUrls)
        {
            var product = await _context.Products
                .Include(p => p.ProductImages)
                .FirstOrDefaultAsync(p => p.Id == productId);

            if (product == null)
            {
                throw new InvalidOperationException($"Product with ID {productId} not found.");
            }

            if (product.ProductImages == null)
            {
                product.ProductImages = new List<ProductImage>();
            }

            foreach (var url in imageUrls)
            {
                // Check if image already exists
                if (!product.ProductImages.Any(img => img.Url == url))
                {
                    product.ProductImages.Add(new ProductImage { Url = url });
                }
            }

            await _context.SaveChangesAsync();
        }

        /// <summary>
        /// Adds the same images to multiple products
        /// </summary>
        public async Task AddImagesToMultipleProductsAsync(List<int> productIds, List<string> imageUrls)
        {
            var products = await _context.Products
                .Include(p => p.ProductImages)
                .Where(p => productIds.Contains(p.Id))
                .ToListAsync();

            foreach (var product in products)
            {
                if (product.ProductImages == null)
                {
                    product.ProductImages = new List<ProductImage>();
                }

                foreach (var url in imageUrls)
                {
                    if (!product.ProductImages.Any(img => img.Url == url))
                    {
                        product.ProductImages.Add(new ProductImage { Url = url });
                    }
                }
            }

            await _context.SaveChangesAsync();
        }

        /// <summary>
        /// Gets all products with their images
        /// </summary>
        public async Task<List<Product>> GetProductsWithImagesAsync()
        {
            return await _context.Products
                .Include(p => p.ProductImages)
                .ToListAsync();
        }

        /// <summary>
        /// Removes an image from a product
        /// </summary>
        public async Task RemoveImageFromProductAsync(int productId, int imageId)
        {
            var product = await _context.Products
                .Include(p => p.ProductImages)
                .FirstOrDefaultAsync(p => p.Id == productId);

            if (product?.ProductImages != null)
            {
                var image = product.ProductImages.FirstOrDefault(img => img.Id == imageId);
                if (image != null)
                {
                    product.ProductImages.Remove(image);
                    await _context.SaveChangesAsync();
                }
            }
        }
    }
}
