import paramiko

def force_start_containers():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== DOCKER START CONTAINERS ===")
    _, out, _ = ssh.exec_command("docker start lpr-postgres lpr-redis lpr-backend lpr-worker lpr-frontend lpr-nginx")
    print(out.read().decode('utf-8'))
    
    ssh.close()

force_start_containers()
