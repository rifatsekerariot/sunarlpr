import paramiko

def check_backend_real_crash():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== EXECUTING PYTHON DIRECTLY IN CONTAINER ===")
    _, out, _ = ssh.exec_command("docker exec lpr-backend python -c 'import app.main; print(\"Import success!\")'")
    print(out.read().decode('utf-8', errors='ignore'))
    
    print("=== RUN LOGS FROM SYSTEMD / DOCKER ===")
    _, out2, _ = ssh.exec_command("docker inspect --format='{{json .State}}' lpr-backend")
    print(out2.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

check_backend_real_crash()
