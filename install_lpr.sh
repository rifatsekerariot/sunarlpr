#!/bin/bash
set -e

echo "===================================================="
echo "          SUNAR LPR - LINUX KURULUM SİHRİBAZI       "
echo "===================================================="

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "[+] Docker bulunamadı. Kurulum başlatılıyor..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    echo "[✓] Docker başarıyla kuruldu."
else
    echo "[✓] Docker zaten yüklü."
fi

# 2. Check for Docker Compose V2
if ! docker compose version &> /dev/null; then
    echo "[+] Docker Compose V2 bulunamadı. Kuruluyor..."
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    echo "[✓] Docker Compose başarıyla kuruldu."
else
    echo "[✓] Docker Compose zaten yüklü."
fi

# 3. Create Project Directory
INSTALL_DIR="/opt/sunar_lpr"
echo "[+] Proje dizini oluşturuluyor: $INSTALL_DIR"
sudo mkdir -p "$INSTALL_DIR"
sudo chown -R $USER:$USER "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 4. Download docker-compose.yml from Repository
echo "[+] Docker Compose dosyası indiriliyor..."
curl -sSL https://raw.githubusercontent.com/rifatsekerariot/sunarlpr/main/docker-compose.yml -o docker-compose.yml

# 5. Create/Configure .env file
if [ ! -f .env ]; then
    echo "[+] .env yapılandırma dosyası oluşturuluyor..."
    curl -sSL https://raw.githubusercontent.com/rifatsekerariot/sunarlpr/main/.env.example -o .env
    
    # Prompt for database password
    read -sp "Veritabanı şifresini belirleyin (Default: lpr_password): " DB_PASS
    echo ""
    if [ ! -z "$DB_PASS" ]; then
        sed -i "s/lpr_password/$DB_PASS/g" .env
    fi
fi

# 6. Run Stack
echo "[+] Sunar LPR konteynerleri indiriliyor ve çalıştırılıyor..."
docker compose pull || echo "Geliştirici uyarısı: İmajlar lokalde derleniyor..."
docker compose up -d --build

echo "===================================================="
echo "[✓] Kurulum Tamamlandı!"
echo "Sunar LPR Servisleri aktif durumda."
echo "Tarayıcınızdan http://localhost adresine giderek erişebilirsiniz."
echo "===================================================="
