import paramiko

def start_containers():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== STARTING THE CREATED CONTAINERS ===")
    ssh.exec_command("docker start lpr-backend lpr-worker lpr-frontend lpr-nginx")
    
    import time
    time.sleep(5)
    
    _, out, _ = ssh.exec_command("docker ps -a")
    print(out.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

start_containers()
