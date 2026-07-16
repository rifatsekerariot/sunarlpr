import paramiko
import sys

def test_remote_login():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    # Test POST login using curl on remote host
    print("Testing local container login API...")
    stdin, stdout, stderr = ssh.exec_command("docker exec -T lpr-backend curl -s -X POST http://localhost:8000/api/auth/login -d 'username=admin&password=admin123'")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    test_remote_login()
