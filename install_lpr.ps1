Write-Host "====================================================" -ForegroundColor Green
Write-Host "         SUNAR LPR - WINDOWS KURULUM SİHRİBAZI      " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

# 1. Check Admin Privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "Lütfen bu scripti yönetici (Administrator) yetkileriyle çalıştırın!"
    Exit
}

# 2. Check for Docker Desktop
$dockerCheck = Get-Command docker -ErrorAction SilentlyContinue
if ($null -eq $dockerCheck) {
    Write-Host "[+] Docker Desktop bulunamadı. Kurulum başlatılıyor (winget)..." -ForegroundColor Yellow
    winget install Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
    Write-Host "[!] Lütfen bilgisayarınızı yeniden başlatın veya Docker'ı açıp tekrar deneyin." -ForegroundColor Red
    Exit
}
Write-Host "[✓] Docker zaten yüklü." -ForegroundColor Green

# 3. Create Project Directory
$installDir = "C:\sunar_lpr"
if (-not (Test-Path $installDir)) {
    Write-Host "[+] Proje dizini oluşturuluyor: $installDir"
    New-Item -ItemType Directory -Path $installDir | Out-Null
}
Set-Location $installDir

# 4. Download docker-compose.yml
Write-Host "[+] Docker Compose dosyası indiriliyor..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/rifatsekerariot/sunarlpr/main/docker-compose.yml" -OutFile "docker-compose.yml"

# 5. Create/Configure .env file
if (-not (Test-Path ".env")) {
    Write-Host "[+] .env yapılandırma dosyası oluşturuluyor..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/rifatsekerariot/sunarlpr/main/.env.example" -OutFile ".env"
    
    $dbPass = Read-Host 'Veritabanı şifresini belirleyin (Varsayılan: lpr_password)'
    if ($dbPass) {
        (Get-Content .env) -replace "lpr_password", $dbPass | Set-Content .env
    }
}

# 6. Run Stack
Write-Host "[+] Sunar LPR konteynerleri indiriliyor ve çalıştırılıyor..." -ForegroundColor Cyan
docker compose pull
docker compose up -d --build

Write-Host "====================================================" -ForegroundColor Green
Write-Host "[✓] Kurulum Başarıyla Tamamlandı!" -ForegroundColor Green
Write-Host "Servislere tarayıcınızdan http://localhost adresinden erişebilirsiniz." -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
