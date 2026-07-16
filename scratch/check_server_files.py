import paramiko

def check_server_files():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== FILES IN /var/www/sunar_lpr ===")
    _, out1, _ = ssh.exec_command("ls -la /var/www/sunar_lpr")
    print(out1.read().decode('utf-8', errors='ignore'))
    
    print("=== DOCKER LOGS SHORT LAST ===")
    _, out2, _ = ssh.exec_command("docker logs lpr-backend --tail 100")
    print(out2.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

check_server_files()
