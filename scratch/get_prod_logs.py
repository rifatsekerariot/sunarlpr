import paramiko
import sys

def get_logs():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("docker compose -f /var/www/sunar_lpr/docker-compose.yml logs backend --tail 30")
    print(stdout.read().decode())
    print(stderr.read().decode())
    ssh.close()

if __name__ == "__main__":
    get_logs()
