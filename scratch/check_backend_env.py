import paramiko

def check_backend_env():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== DOCKER COMPOSE CONFIG ENV ===")
    _, out, _ = ssh.exec_command("docker compose config")
    print(out.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

check_backend_env()
