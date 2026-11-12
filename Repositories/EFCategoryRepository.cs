using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Threading.Tasks;
using TH3.Models;

public class EFCategoryRepository : ICategoryRepository
{
    private readonly ApplicationDbContext _context;

    public EFCategoryRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<IEnumerable<Category>> GetAllAsync()
    {
        // Sử dụng AsNoTracking để tăng tốc độ truy vấn khi chỉ đọc danh sách
        return await _context.Categories.AsNoTracking().ToListAsync();
    }

    public async Task<Category> GetByIdAsync(int id)
    {
        // Thay FindAsync bằng FirstOrDefaultAsync để nhất quán và dễ mở rộng
        return await _context.Categories
            .FirstOrDefaultAsync(c => c.Id == id);
    }

    public async Task AddAsync(Category category)
    {
        _context.Categories.Add(category);
        await _context.SaveChangesAsync();
    }

    public async Task UpdateAsync(Category category)
    {
        _context.Categories.Update(category);
        await _context.SaveChangesAsync();
    }

    public async Task DeleteAsync(int id)
    {
        var category = await _context.Categories.FindAsync(id);

        // Bổ sung kiểm tra null để bảo vệ ứng dụng khỏi lỗi crash
        if (category != null)
        {
            _context.Categories.Remove(category);
            await _context.SaveChangesAsync();
        }
    }
}