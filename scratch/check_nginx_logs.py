import paramiko

def check_nginx_logs():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== NGINX CONTAINER ERROR LOGS ===")
    _, out, _ = ssh.exec_command("docker logs lpr-nginx --tail 30")
    print(out.read().decode('utf-8', errors='ignore'))
    
    print("=== SYSTEM NGINX ERROR LOGS ===")
    _, out2, _ = ssh.exec_command("tail -n 30 /var/log/nginx/error.log")
    print(out2.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

check_nginx_logs()
