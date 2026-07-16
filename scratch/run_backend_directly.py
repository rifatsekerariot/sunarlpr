import paramiko

def run_backend_directly():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== RUNNING ENTRYPOINT MANUALLY TO SPOT THE CRASH ===")
    _, out, _ = ssh.exec_command("docker exec lpr-backend ./entrypoint.sh || docker run --entrypoint ./entrypoint.sh --network sunar_default sunar_lpr-backend")
    print(out.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

run_backend_directly()
