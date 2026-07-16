import paramiko
import sys

def check_worker_logs():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    _, out, _ = ssh.exec_command("docker logs lpr-worker --tail 30 2>&1")
    text = out.read().decode('utf-8', errors='ignore')
    # Use stdout write with replacement to bypass cp1254 terminal limits
    sys.stdout.buffer.write(text.encode('ascii', errors='replace'))
    print()
    ssh.close()

check_worker_logs()
