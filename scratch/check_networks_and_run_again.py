import paramiko

def check_networks_and_run_again():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== DOCKER RUN DIRECT DEBUG WITH CORRECT NET ===")
    # Network on server is sunar_lpr_default
    stdin, stdout, stderr = ssh.exec_command("docker run --rm --network sunar_lpr_default -e DATABASE_URL=postgresql+asyncpg://lpr_user:lpr_pass123@lpr-postgres:5432/lpr_db -e REDIS_URL=redis://lpr-redis:6379/0 sunar_lpr-backend uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("STDOUT:")
    print(stdout.read().decode('utf-8', errors='ignore'))
    print("STDERR:")
    print(stderr.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

check_networks_and_run_again()
