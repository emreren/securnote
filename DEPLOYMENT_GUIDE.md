# SecurNote SSH Server Deployment Guide

Bu rehber SecurNote'u uzak sunucuda SSH erişimi ile kurmanız için hazırlanmıştır.

## 📋 Özellikler

- **SSH Tabanlı Erişim**: Güvenli SSH bağlantısı ile uzaktan not yönetimi
- **End-to-End Şifreleme**: Notlar client tarafında şifrelenir
- **Multi-User Support**: Birden fazla kullanıcı desteği
- **Terminal Interface**: Komut satırı ve interaktif mod
- **Docker Deployment**: Kolay kurulum ve yönetim

## 🚀 Kurulum Yöntemleri

### Yöntem 1: Docker ile Kurulum (Önerilen)

#### 1. Projeyi Klonlayın
```bash
git clone https://github.com/emreren/securnote.git
cd securnote
```

#### 2. SSH Anahtarlarını Hazırlayın
```bash
# SSH anahtarları için dizin oluşturun
mkdir -p ssh_keys

# Public key'inizi kopyalayın
cp ~/.ssh/id_rsa.pub ssh_keys/authorized_keys

# Veya manuel olarak ekleyin
echo "ssh-rsa AAAAB3NzaC1yc2E... your-email@domain.com" >> ssh_keys/authorized_keys
```

#### 3. Docker Container'ı Başlatın
```bash
# SSH server'ı başlatın
docker-compose -f docker-compose.ssh.yml up -d

# Logları kontrol edin
docker-compose -f docker-compose.ssh.yml logs -f securnote-ssh
```

#### 4. Bağlantıyı Test Edin
```bash
# Bağlantı testi
ssh securnote@localhost -p 2222 securnote

# Veya connection script kullanın
./scripts/connect_remote.sh -p 2222 localhost
```

### Yöntem 2: Manual Kurulum

#### 1. Sunucuda Setup Script'i Çalıştırın
```bash
# Script'i sunucuya kopyalayın
scp scripts/server_setup.sh user@your-server:/tmp/

# Sunucuda çalıştırın
ssh user@your-server
sudo chmod +x /tmp/server_setup.sh
sudo /tmp/server_setup.sh
```

#### 2. SSH Anahtarlarını Ekleyin
```bash
# Sunucuda
sudo mkdir -p /home/securnote/.ssh
echo "your-public-key-here" | sudo tee /home/securnote/.ssh/authorized_keys
sudo chown -R securnote:securnote /home/securnote/.ssh
sudo chmod 700 /home/securnote/.ssh
sudo chmod 600 /home/securnote/.ssh/authorized_keys
```

## 🔧 Kullanım

### İnteraktif Mod
```bash
# Sunucuya bağlanın ve interaktif modu başlatın
ssh securnote@your-server securnote

# Veya client script ile
./scripts/connect_remote.sh your-server
```

### Komut Satırı Modu
```bash
# Kullanıcı kaydet
ssh securnote@your-server 'securnote register alice password123'

# Notları listele
ssh securnote@your-server 'securnote list alice password123'

# Not görüntüle
ssh securnote@your-server 'securnote view alice password123 note-id'

# Not ekle
ssh securnote@your-server 'securnote add alice password123 "My Note" "Note content"'

# Not sil
ssh securnote@your-server 'securnote delete alice password123 note-id'
```

### Client Script ile Gelişmiş Kullanım
```bash
# Bağlantı scripti ile
./scripts/connect_remote.sh your-server

# Custom SSH ayarları ile
./scripts/connect_remote.sh -u myuser -p 2222 -k ~/.ssh/my_key your-server

# Direkt komut çalıştırma
./scripts/connect_remote.sh your-server list alice password123
```

## 🔐 Güvenlik

### SSH Güvenliği
- Password authentication devre dışı
- Sadece public key authentication
- Custom SSH port kullanımı önerilir
- Firewall'da sadece SSH portu açık olmalı

### Veri Güvenliği
- Notlar client tarafında AES-256 ile şifrelenir
- Sunucu sadece şifreli veri görür
- Şifreleme anahtarları asla sunucuya gönderilmez
- Her kullanıcının kendi şifreleme anahtarı vardır

## 📁 Dosya Yapısı

```
Sunucuda:
/opt/securnote/          # Uygulama dosyaları
/home/securnote/         # Kullanıcı dizini
├── .securnote/          # Şifreli notlar
├── .ssh/                # SSH anahtarları
└── securnote            # CLI script

Docker'da:
/home/securnote/.securnote/  # Data volume
```

## 🛠️ Yönetim

### Docker Yönetimi
```bash
# Container'ı durdur
docker-compose -f docker-compose.ssh.yml down

# Yeniden başlat
docker-compose -f docker-compose.ssh.yml restart

# Logları görüntüle
docker-compose -f docker-compose.ssh.yml logs -f

# Container'a erişim
docker exec -it securnote-ssh-server bash
```

### Backup
```bash
# Data backup (Docker)
docker run --rm -v securnote_data:/data -v $(pwd):/backup alpine tar czf /backup/securnote-backup.tar.gz -C /data .

# Data restore (Docker)
docker run --rm -v securnote_data:/data -v $(pwd):/backup alpine tar xzf /backup/securnote-backup.tar.gz -C /data
```

### SSH Anahtar Yönetimi
```bash
# Yeni anahtar ekle
echo "ssh-rsa AAAAB3NzaC1yc2E... new-user@domain.com" >> ssh_keys/authorized_keys
docker-compose -f docker-compose.ssh.yml restart securnote-ssh

# Manuel olarak container'da
docker exec -it securnote-ssh-server bash
echo "new-public-key" >> /home/securnote/.ssh/authorized_keys
```

## 🚨 Sorun Giderme

### Bağlantı Sorunları
```bash
# SSH bağlantı testi
ssh -v securnote@your-server -p 2222

# Container logları
docker logs securnote-ssh-server

# SSH service durumu
docker exec securnote-ssh-server systemctl status ssh
```

### Uygulama Sorunları
```bash
# CLI test
docker exec -it securnote-ssh-server sudo -u securnote securnote

# Permissions kontrolü
docker exec securnote-ssh-server ls -la /home/securnote/.securnote
```

### Performance Tuning
```bash
# SSH connection limit ayarları
# /etc/ssh/sshd_config'de:
MaxStartups 10:30:100
ClientAliveInterval 60
ClientAliveCountMax 3
```

## 📊 Monitoring

### Health Check
```bash
# Container health
docker ps
docker inspect securnote-ssh-server | grep Health

# Application health
ssh securnote@your-server 'securnote list test test 2>/dev/null && echo "OK" || echo "FAIL"'
```

### Logs
```bash
# SSH logs
docker exec securnote-ssh-server tail -f /var/log/auth.log

# Application logs
docker logs -f securnote-ssh-server
```

## 🔄 Updates

### Uygulama Güncellemesi
```bash
# Kodu güncelle
git pull

# Container'ı yeniden build et
docker-compose -f docker-compose.ssh.yml build --no-cache

# Yeniden başlat
docker-compose -f docker-compose.ssh.yml up -d
```

## 🌐 Production Deployment

### Domain ve SSL
```bash
# Nginx reverse proxy örneği
# /etc/nginx/sites-available/securnote
upstream securnote_ssh {
    server localhost:2222;
}

server {
    listen 22;
    server_name notes.yourdomain.com;

    location / {
        proxy_pass tcp://securnote_ssh;
        proxy_timeout 1s;
        proxy_responses 1;
    }
}
```

### Firewall
```bash
# ufw firewall kuralları
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 2222/tcp   # SecurNote SSH (if different port)
sudo ufw enable
```

Bu rehber ile SecurNote'u güvenli bir şekilde uzak sunucuda kurabilir ve kullanabilirsiniz!