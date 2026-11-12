using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.StaticFiles;
using TH3.Models;
using TH3.Services;

var builder = WebApplication.CreateBuilder(args);

// DATABASE

builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(
        builder.Configuration.GetConnectionString("DefaultConnection")));

// IDENTITY

builder.Services.AddIdentity<ApplicationUser, IdentityRole>()
    .AddDefaultTokenProviders()
    .AddDefaultUI()
    .AddEntityFrameworkStores<ApplicationDbContext>();

builder.Services.ConfigureApplicationCookie(options =>
{
    options.LoginPath = "/Identity/Account/Login";
    options.LogoutPath = "/Identity/Account/Logout";
    options.AccessDeniedPath = "/Identity/Account/AccessDenied";
});

// MVC

builder.Services.AddControllersWithViews();

builder.Services.AddRazorPages();

// SESSION

builder.Services.AddDistributedMemoryCache();

builder.Services.AddSession(options =>
{
    options.IdleTimeout = TimeSpan.FromMinutes(30);

    options.Cookie.HttpOnly = true;

    options.Cookie.IsEssential = true;
});

// SERVICES

builder.Services.AddHttpClient();

builder.Services.AddScoped<IProductRepository, EFProductRepository>();

builder.Services.AddScoped<ICategoryRepository, EFCategoryRepository>();

builder.Services.AddScoped<ImageSeedingService>();
builder.Services.AddScoped<DatabaseSeedingService>();
builder.Services.AddScoped<RecommendationService>();
// SIGNALR

builder.Services.AddSignalR();

var app = builder.Build();

// PIPELINE

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");

    app.UseHsts();
}

app.UseHttpsRedirection();

var staticContentTypes = new FileExtensionContentTypeProvider();
staticContentTypes.Mappings[".glb"] = "model/gltf-binary";
app.UseStaticFiles(new StaticFileOptions
{
    ContentTypeProvider = staticContentTypes
});

app.UseRouting();

app.UseSession();

app.UseAuthentication();

app.UseAuthorization();

// SIGNALR

app.MapHub<TH3.Hubs.ChatHub>("/chatHub");

// AREA

app.MapControllerRoute(
    name: "Admin",
    pattern: "{area:exists}/{controller=Home}/{action=Index}/{id?}");

// DEFAULT

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

// RAZOR

app.MapRazorPages();

// SEED CLASSIFIED PRODUCTS (Ốp lưng OL, iPhone IP, Samsung SS, etc.)
try
{
    using var scope = app.Services.CreateScope();
    var seeder = scope.ServiceProvider.GetRequiredService<DatabaseSeedingService>();
    await seeder.SeedClassifiedProductsAsync();
}
catch { }

app.Run();