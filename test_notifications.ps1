# Test Notification Script for KileKitabu Backend
# Usage: .\test_notifications.ps1

$BASE_URL = "http://localhost:5000"  # Change to your Render.com URL for production
$USER_ID = "GI7PPaaRh7hRogozJcDHt33RQEw2"

Write-Host "🧪 Testing KileKitabu Notifications" -ForegroundColor Cyan
Write-Host ""

# Test 1: Send individual test notification
Write-Host "1️⃣ Testing individual notification..." -ForegroundColor Yellow
$body = @{
    user_id = $USER_ID
    title = "Test Notification"
    body = "This is a test notification from KileKitabu backend. If you receive this, notifications are working!"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/notifications/test/send" -Method POST -Body $body -ContentType "application/json"
    Write-Host "✅ Success: $($response.message)" -ForegroundColor Green
    Write-Host "   User ID: $($response.user_id)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Test low credit notifications
Write-Host "2️⃣ Testing low credit notifications..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/notifications/test/low-credit" -Method POST
    Write-Host "✅ Success: $($response.message)" -ForegroundColor Green
    Write-Host "   Check backend logs for detailed results" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Test debt reminder notifications
Write-Host "3️⃣ Testing debt reminder notifications..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/notifications/test/debt-reminders" -Method POST
    Write-Host "✅ Success: $($response.message)" -ForegroundColor Green
    Write-Host "   Check backend logs for detailed results" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Check keep-alive endpoint
Write-Host "4️⃣ Testing keep-alive endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/health/keep-alive" -Method GET
    Write-Host "✅ Success: $($response.status)" -ForegroundColor Green
    Write-Host "   Message: $($response.message)" -ForegroundColor Gray
    Write-Host "   Timestamp: $($response.timestamp)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "✨ All tests completed!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 Check your device for notifications" -ForegroundColor Yellow
Write-Host "📋 Check backend logs for detailed results" -ForegroundColor Yellow

