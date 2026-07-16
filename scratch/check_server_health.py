import paramiko

def check_server_health():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== DOCKER STATUS AFTER 10 SECONDS ===")
    _, out1, _ = ssh.exec_command("docker ps -a")
    print(out1.read().decode('utf-8', errors='ignore'))
    
    print("=== WORKER LOGS ===")
    _, out2, _ = ssh.exec_command("docker logs lpr-worker")
    print(out2.read().decode('utf-8', errors='ignore'))
    
    print("=== BACKEND LOGS ===")
    _, out3, _ = ssh.exec_command("docker logs lpr-backend")
    print(out3.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

check_server_health()
