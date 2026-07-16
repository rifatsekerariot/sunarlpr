import paramiko

def force_start_containers():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== FORCE RESTARTING ALL CONTAINERS TO MAKE SURE WORKER/FRONTEND START CLEAN ===")
    ssh.exec_command("cd /var/www/sunar_lpr && docker compose down && docker compose up -d")
    
    import time
    time.sleep(5)
    
    _, out, _ = ssh.exec_command("docker ps -a")
    print(out.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

force_start_containers()
