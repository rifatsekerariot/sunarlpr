import paramiko

def check_networks_and_run():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== DOCKER NETWORKS ===")
    _, out, _ = ssh.exec_command("docker network ls")
    print(out.read().decode('utf-8', errors='ignore'))
    
    print("=== DOCKER RUN DIRECT DEBUG WITH CORRECT NET ===")
    # Network on server is sunarlpr_default
    _, out2, _ = ssh.exec_command("docker run --rm --network sunarlpr_default -e DATABASE_URL=postgresql+asyncpg://lpr_user:lpr_pass123@lpr-postgres:5432/lpr_db -e REDIS_URL=redis://lpr-redis:6379/0 sunar_lpr-backend uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print(out2.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

check_networks_and_run()
