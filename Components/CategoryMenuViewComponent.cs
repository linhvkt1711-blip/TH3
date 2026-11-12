using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using TH3.Models;

namespace TH3.Components
{
    public class CategoryMenuViewComponent : ViewComponent
    {
        private readonly IServiceScopeFactory _scopeFactory;

        public CategoryMenuViewComponent(IServiceScopeFactory scopeFactory)
        {
            _scopeFactory = scopeFactory;
        }

        public async Task<IViewComponentResult> InvokeAsync()
        {
            IEnumerable<Category> categories = Enumerable.Empty<Category>();

            try
            {
                using var scope = _scopeFactory.CreateScope();
                var categoryRepository = scope.ServiceProvider.GetRequiredService<ICategoryRepository>();
                categories = await categoryRepository.GetAllAsync() ?? Enumerable.Empty<Category>();
            }
            catch (ObjectDisposedException)
            {
                categories = Enumerable.Empty<Category>();
            }
            catch (Exception)
            {
                categories = Enumerable.Empty<Category>();
            }

            return View(categories);
        }
    }
}