using Microsoft.AspNetCore.SignalR;
using System.Collections.Concurrent;
 
namespace TH3.Hubs
{
    public class ChatHub : Hub
    {
        // Lưu mapping: connectionId -> userId/sessionId
        private static readonly ConcurrentDictionary<string, string> _userConnections = new();
        // Lưu mapping: sessionId -> list messages chờ admin
        private static readonly ConcurrentDictionary<string, List<ChatMessage>> _pendingMessages = new();
 
        public override async Task OnConnectedAsync()
        {
            var httpContext = Context.GetHttpContext();
            var userId = httpContext?.User?.Identity?.Name ?? Context.ConnectionId;
            var sessionId = httpContext?.Request.Query["sessionId"].ToString() ?? Context.ConnectionId;
 
            _userConnections[Context.ConnectionId] = sessionId;
 
            // Nếu là admin thì join group admin
            if (httpContext?.User?.IsInRole("Admin") == true || 
                httpContext?.Request.Query["role"].ToString() == "admin")
            {
                await Groups.AddToGroupAsync(Context.ConnectionId, "Admins");
                // Gửi danh sách các session đang chờ
                var sessions = _pendingMessages.Keys.ToList();
                await Clients.Caller.SendAsync("ActiveSessions", sessions);
            }
            else
            {
                // User thường - gửi welcome
                await Clients.Caller.SendAsync("BotMessage", new
                {
                    message = "Xin chào! Tôi là trợ lý AI của shop. Bạn có thể:\n• Mô tả điện thoại bạn muốn tìm\n• Hỏi về sản phẩm, giá cả\n• Gõ <b>chat admin</b> để trò chuyện trực tiếp với admin",
                    timestamp = DateTime.Now.ToString("HH:mm"),
                    isBot = true
                });
            }
 
            await base.OnConnectedAsync();
        }
 
        public override async Task OnDisconnectedAsync(Exception? exception)
        {
            _userConnections.TryRemove(Context.ConnectionId, out _);
            await base.OnDisconnectedAsync(exception);
        }
 
        // User gửi message
        public async Task SendUserMessage(string sessionId, string message, bool wantAdmin)
        {
            var msg = new ChatMessage
            {
                SessionId = sessionId,
                Message = message,
                Timestamp = DateTime.Now,
                IsUser = true
            };
 
            if (wantAdmin)
            {
                // Lưu vào pending và notify admin
                if (!_pendingMessages.ContainsKey(sessionId))
                    _pendingMessages[sessionId] = new List<ChatMessage>();
                _pendingMessages[sessionId].Add(msg);
 
                // Gửi cho tất cả admin
                await Clients.Group("Admins").SendAsync("UserMessage", new
                {
                    sessionId = sessionId,
                    message = message,
                    timestamp = DateTime.Now.ToString("HH:mm"),
                    connectionId = Context.ConnectionId
                });
            }
 
            // Echo lại cho user
            await Clients.Caller.SendAsync("MessageSent", new
            {
                message = message,
                timestamp = DateTime.Now.ToString("HH:mm")
            });
        }
 
        // Admin trả lời user
        public async Task AdminReply(string targetSessionId, string message)
        {
            // Tìm connectionId của user có sessionId đó
            var userConn = _userConnections.FirstOrDefault(x => x.Value == targetSessionId);
            if (userConn.Key != null)
            {
                await Clients.Client(userConn.Key).SendAsync("AdminMessage", new
                {
                    message = message,
                    timestamp = DateTime.Now.ToString("HH:mm"),
                    isAdmin = true
                });
            }
 
            // Confirm cho admin
            await Clients.Caller.SendAsync("ReplySent", new
            {
                sessionId = targetSessionId,
                message = message,
                timestamp = DateTime.Now.ToString("HH:mm")
            });
        }
 
        // Admin join session cụ thể
        public async Task JoinSession(string sessionId)
        {
            await Groups.AddToGroupAsync(Context.ConnectionId, $"session_{sessionId}");
            
            // Gửi lịch sử chat
            if (_pendingMessages.TryGetValue(sessionId, out var history))
            {
                await Clients.Caller.SendAsync("ChatHistory", new
                {
                    sessionId = sessionId,
                    messages = history.Select(m => new
                    {
                        message = m.Message,
                        timestamp = m.Timestamp.ToString("HH:mm"),
                        isUser = m.IsUser
                    })
                });
            }
        }
 
        // Thông báo user rằng admin đã tham gia
        public async Task NotifyUserAdminJoined(string sessionId)
        {
            var userConn = _userConnections.FirstOrDefault(x => x.Value == sessionId);
            if (userConn.Key != null)
            {
                await Clients.Client(userConn.Key).SendAsync("AdminJoined", new
                {
                    message = "Admin đã tham gia cuộc trò chuyện. Bạn có thể chat trực tiếp!",
                    timestamp = DateTime.Now.ToString("HH:mm")
                });
            }
        }
    }
 
    public class ChatMessage
    {
        public string SessionId { get; set; } = "";
        public string Message { get; set; } = "";
        public DateTime Timestamp { get; set; }
        public bool IsUser { get; set; }
    }
}