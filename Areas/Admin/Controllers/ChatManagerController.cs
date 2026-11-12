using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
 
namespace TH3.Areas.Admin.Controllers
{
    [Area("Admin")]
    [Authorize(Roles = "Admin")]
    public class ChatManagerController : Controller
    {
        public IActionResult Index()
        {
            ViewData["Title"] = "Quản lý Chat";
            return View();
        }
    }
}
 