using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using TH3.Models;
using TH3.Services;

namespace TH3.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    [Authorize(Roles = "Admin")]
    public class ImageManagementController : ControllerBase
    {
        private readonly ImageSeedingService _imageSeedingService;
        private readonly IProductRepository _productRepository;

        public ImageManagementController(ImageSeedingService imageSeedingService, IProductRepository productRepository)
        {
            _imageSeedingService = imageSeedingService;
            _productRepository = productRepository;
        }

        /// <summary>
        /// Add images to a specific product
        /// </summary>
        [HttpPost("add-to-product/{productId}")]
        public async Task<IActionResult> AddImagesToProduct(int productId, [FromBody] List<string> imageUrls)
        {
            try
            {
                await _imageSeedingService.AddImagesToProductAsync(productId, imageUrls);
                return Ok(new { message = $"Added {imageUrls.Count} images to product {productId}" });
            }
            catch (InvalidOperationException ex)
            {
                return NotFound(new { error = ex.Message });
            }
            catch (Exception ex)
            {
                return BadRequest(new { error = ex.Message });
            }
        }

        /// <summary>
        /// Add images to multiple products
        /// </summary>
        [HttpPost("add-to-products")]
        public async Task<IActionResult> AddImagesToMultipleProducts([FromBody] BulkImageRequest request)
        {
            try
            {
                if (request?.ProductIds == null || request.ImageUrls == null || request.ProductIds.Count == 0 || request.ImageUrls.Count == 0)
                {
                    return BadRequest(new { error = "ProductIds and ImageUrls cannot be empty" });
                }

                await _imageSeedingService.AddImagesToMultipleProductsAsync(request.ProductIds, request.ImageUrls);
                return Ok(new { message = $"Added {request.ImageUrls.Count} images to {request.ProductIds.Count} products" });
            }
            catch (Exception ex)
            {
                return BadRequest(new { error = ex.Message });
            }
        }

        /// <summary>
        /// Get all products with their images
        /// </summary>
        [HttpGet("products-with-images")]
        [AllowAnonymous]
        public async Task<IActionResult> GetProductsWithImages()
        {
            try
            {
                var products = await _imageSeedingService.GetProductsWithImagesAsync();
                return Ok(products);
            }
            catch (Exception ex)
            {
                return BadRequest(new { error = ex.Message });
            }
        }

        /// <summary>
        /// Remove an image from a product
        /// </summary>
        [HttpDelete("remove-image/{productId}/{imageId}")]
        public async Task<IActionResult> RemoveImage(int productId, int imageId)
        {
            try
            {
                await _imageSeedingService.RemoveImageFromProductAsync(productId, imageId);
                return Ok(new { message = "Image removed successfully" });
            }
            catch (Exception ex)
            {
                return BadRequest(new { error = ex.Message });
            }
        }
    }

    public class BulkImageRequest
    {
        public List<int>? ProductIds { get; set; }
        public List<string>? ImageUrls { get; set; }
    }
}
