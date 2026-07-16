import paramiko
import sys

def seed_db():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    print("Seeding database with python path set...")
    stdin, stdout, stderr = ssh.exec_command("docker compose -f /var/www/sunar_lpr/docker-compose.yml exec -T backend python -c \"import sys; sys.path.append('/app'); import app.seed\"")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    seed_db()
