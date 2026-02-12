# Quick Deployment Helper Script
# This script helps you deploy to GitHub and Streamlit Cloud

Write-Host "🚀 Address Geocoding System - Deployment Helper" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git initialized" -ForegroundColor Green
} else {
    Write-Host "✅ Git already initialized" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create a GitHub repository:" -ForegroundColor White
Write-Host "   - Go to https://github.com/new" -ForegroundColor Gray
Write-Host "   - Name: address-geocoding-system" -ForegroundColor Gray
Write-Host "   - Make it PUBLIC (required for free Streamlit Cloud)" -ForegroundColor Gray
Write-Host "   - Don't initialize with README" -ForegroundColor Gray
Write-Host ""

Write-Host "2. After creating the repo, run these commands:" -ForegroundColor White
Write-Host ""
Write-Host "   git add ." -ForegroundColor Yellow
Write-Host "   git commit -m ""Initial commit - Address Geocoding System""" -ForegroundColor Yellow
Write-Host "   git remote add origin https://github.com/YOUR-USERNAME/address-geocoding-system.git" -ForegroundColor Yellow
Write-Host "   git branch -M main" -ForegroundColor Yellow
Write-Host "   git push -u origin main" -ForegroundColor Yellow
Write-Host ""

Write-Host "3. Deploy on Streamlit Cloud:" -ForegroundColor White
Write-Host "   - Go to https://share.streamlit.io" -ForegroundColor Gray
Write-Host "   - Sign in with GitHub" -ForegroundColor Gray
Write-Host "   - Click 'New app'" -ForegroundColor Gray
Write-Host "   - Select your repository" -ForegroundColor Gray
Write-Host "   - Main file: interfaces/streamlit_app.py" -ForegroundColor Gray
Write-Host "   - Click Deploy!" -ForegroundColor Gray
Write-Host ""

Write-Host "📖 For detailed instructions, see DEPLOYMENT.md" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to proceed with git add
$response = Read-Host "Would you like to add all files to git now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    Write-Host "📦 Adding files to git..." -ForegroundColor Yellow
    git add .
    Write-Host "✅ Files added" -ForegroundColor Green
    Write-Host ""
    Write-Host "Now run: git commit -m ""Initial commit""" -ForegroundColor Yellow
}
