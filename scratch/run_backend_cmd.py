import paramiko

def run_backend_cmd():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== DOCKER RUN DIRECT DEBUG ===")
    _, out, _ = ssh.exec_command("docker run --rm --network sunar_default -e DATABASE_URL=postgresql+asyncpg://lpr-user:lpr-pass123@lpr-postgres:5432/lpr_db -e REDIS_URL=redis://lpr-redis:6379/0 sunar_lpr-backend uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print(out.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

run_backend_cmd()
