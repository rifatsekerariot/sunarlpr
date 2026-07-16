import paramiko

def run_backend_interactive():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== DOCKER START AND ATTACH FOR ERROR DIAGNOSTICS ===")
    _, out, _ = ssh.exec_command("docker stop lpr-backend && docker run --name lpr-backend-debug --rm --network sunar_default -e DATABASE_URL=postgresql+asyncpg://lpr_user:lpr_pass123@lpr-postgres:5432/lpr_db -e REDIS_URL=redis://lpr-redis:6379/0 sunar_lpr-backend ./entrypoint.sh")
    print(out.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

run_backend_interactive()
