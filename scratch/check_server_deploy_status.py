import paramiko

def check_server_deploy_status():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== DEPLOY FOLDER COMPOSE DOWNS ===")
    _, out1, _ = ssh.exec_command("docker ps -a")
    print(out1.read().decode('utf-8', errors='ignore'))
    
    print("=== RECENT DOCKER LOGS FOR BACKEND ===")
    _, out2, _ = ssh.exec_command("docker logs lpr-backend --tail 30")
    print(out2.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

check_server_deploy_status()
