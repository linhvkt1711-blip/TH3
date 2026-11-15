using Microsoft.AspNetCore.Identity.UI.Services;

namespace TH3.Services
{
    public class IdentityEmailSender : IEmailSender
    {
        private readonly ILogger<IdentityEmailSender> _logger;

        public IdentityEmailSender(ILogger<IdentityEmailSender> logger)
        {
            _logger = logger;
        }

        public Task SendEmailAsync(string email, string subject, string htmlMessage)
        {
            _logger.LogInformation("[Identity Email] To: {Email} | Subject: {Subject}", email, subject);
            return Task.CompletedTask;
        }
    }
}
