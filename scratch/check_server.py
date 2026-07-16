import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('200.97.171.59', username='root', password='XgzF2A@LWmMhA-kQ', timeout=15, banner_timeout=15)

cmds = [
    ("Konteyner durumu", "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"),
    ("Nginx durumu", "systemctl is-active nginx && nginx -t 2>&1 | tail -3"),
    ("Backend son log", "docker logs lpr-backend --tail 10 2>&1"),
    ("Frontend son log", "docker logs lpr-frontend --tail 5 2>&1"),
    ("Nginx son log", "docker logs lpr-nginx --tail 5 2>&1"),
    ("Port 80/443 dinleme", "ss -tlnp | grep -E ':80|:443|:8085'"),
]

for label, cmd in cmds:
    _, out, err = ssh.exec_command(cmd)
    result = (out.read() + err.read()).decode().strip()
    print(f"\n=== {label} ===")
    print(result or "(boş)")

ssh.close()
