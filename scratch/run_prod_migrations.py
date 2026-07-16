import paramiko
import sys

def run_migrations():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    # Run alembic upgrade head to set up tables
    print("Running alembic migrations...")
    stdin, stdout, stderr = ssh.exec_command("docker compose -f /var/www/sunar_lpr/docker-compose.yml exec -T backend alembic upgrade head")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    # Add dummy database seeds
    print("Seeding database...")
    stdin, stdout, stderr = ssh.exec_command("docker compose -f /var/www/sunar_lpr/docker-compose.yml exec -T backend python app/seed.py")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    run_migrations()
