import paramiko

def check_tunnel_and_rtsp():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== SUNUCUDA DİNLEYEN PORTLAR ===")
    _, out, _ = ssh.exec_command("ss -tlnp | grep -E '8554|localhost'")
    print(out.read().decode())
    
    print("=== DOCKER CONTAINER İÇİNDEN HOST ERİŞİMİ TESTİ ===")
    # Check if we can ping the forwarded port 8554 from inside worker container
    _, out, err = ssh.exec_command(
        "docker exec lpr-worker python -c 'import socket; s=socket.socket(); s.settimeout(3); s.connect((\"host.docker.internal\", 8554)); print(\"BAGLANTI BASARILI\")' 2>&1"
    )
    print(out.read().decode())
    
    ssh.close()

check_tunnel_and_rtsp()
