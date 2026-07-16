import paramiko

def run_backend_interactive_logs():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== DOCKER START AND ATTACH FOR ERROR DIAGNOSTICS ===")
    # Capture both stdout and stderr by running the container in foreground and reading the stream
    stdin, stdout, stderr = ssh.exec_command("docker run --name lpr-backend-debug-2 --rm --network sunar_default -e DATABASE_URL=postgresql+asyncpg://lpr_user:lpr_pass123@lpr-postgres:5432/lpr_db -e REDIS_URL=redis://lpr-redis:6379/0 sunar_lpr-backend ./entrypoint.sh")
    print("STDOUT:")
    print(stdout.read().decode('utf-8', errors='ignore'))
    print("STDERR:")
    print(stderr.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

run_backend_interactive_logs()
