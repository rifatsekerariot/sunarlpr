import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('200.97.171.59', username='root', password='XgzF2A@LWmMhA-kQ', timeout=15, banner_timeout=15)

print("Docker Compose stack yeniden başlatılıyor...")
_, out, err = ssh.exec_command(
    "cd /var/www/sunar_lpr && docker compose down --remove-orphans 2>&1 && docker compose up -d 2>&1",
    timeout=120
)
print(out.read().decode())
print(err.read().decode())

print("\nKonteyner durumu:")
_, out, _ = ssh.exec_command("docker ps --format 'table {{.Names}}\t{{.Status}}'")
print(out.read().decode())

ssh.close()
