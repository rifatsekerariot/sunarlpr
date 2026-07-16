import paramiko

def check_backend_errors():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== DOCKER INSPECT BACKEND CRASH STATE ===")
    _, out, _ = ssh.exec_command("docker inspect lpr-backend --format '{{.State.Error}} {{.State.ExitCode}}'")
    print(out.read().decode('utf-8', errors='ignore'))
    
    print("=== BACKEND CONTAINER LOGS (STDERR / SYSTEM) ===")
    _, out2, _ = ssh.exec_command("docker logs lpr-backend --tail 50")
    print(out2.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

check_backend_errors()
