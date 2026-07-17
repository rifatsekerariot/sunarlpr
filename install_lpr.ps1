Write-Host "====================================================" -ForegroundColor Green
Write-Host "         SUNAR LPR - WINDOWS INSTALLATION WIZARD     " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

# 1. Check Admin Privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "Please run this script as Administrator!"
    Exit
}

# 2. Check for Docker Desktop
$dockerCheck = Get-Command docker -ErrorAction SilentlyContinue
if ($null -eq $dockerCheck) {
    Write-Host "[+] Docker Desktop not found. Installing via winget..." -ForegroundColor Yellow
    winget install Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
    Write-Host "[!] Please restart your computer or open Docker Desktop and try again." -ForegroundColor Red
    Exit
}
Write-Host "[OK] Docker is already installed." -ForegroundColor Green

# 3. Create Project Directory
$installDir = "C:\sunar_lpr"
if (-not (Test-Path $installDir)) {
    Write-Host "[+] Creating project directory: $installDir"
    New-Item -ItemType Directory -Path $installDir | Out-Null
}
Set-Location $installDir

# 4. Download docker-compose.yml and nginx.conf
Write-Host "[+] Downloading configuration files..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/rifatsekerariot/sunarlpr/main/docker-compose.yml" -OutFile "docker-compose.yml"
if (-not (Test-Path "nginx")) {
    New-Item -ItemType Directory -Path "nginx" | Out-Null
}
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/rifatsekerariot/sunarlpr/main/nginx/nginx.conf" -OutFile "nginx/nginx.conf"

# 5. Create/Configure .env file
if (-not (Test-Path ".env")) {
    Write-Host "[+] Creating .env configuration file..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/rifatsekerariot/sunarlpr/main/.env.example" -OutFile ".env"
    
    $dbPass = Read-Host "Enter database password (Default: lpr_password)"
    if ($dbPass) {
        (Get-Content .env) -replace "lpr_password", $dbPass | Set-Content .env
    }
}

# 6. Run Stack
Write-Host "[+] Pulling and starting Sunar LPR containers..." -ForegroundColor Cyan
docker compose pull
docker compose up -d --build

Write-Host "====================================================" -ForegroundColor Green
Write-Host "[OK] Installation completed successfully!" -ForegroundColor Green
Write-Host "You can access services via http://localhost" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
