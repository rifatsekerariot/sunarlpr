import paramiko

def check_remote():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15, banner_timeout=15)
    
    # Check backend logs for migration and seed output
    print("=== Backend Logs (last 40 lines) ===")
    _, out, _ = ssh.exec_command("docker logs lpr-backend --tail 40 2>&1")
    print(out.read().decode())
    
    # Test login directly inside container
    print("=== Direct Login Test ===")
    _, out, err = ssh.exec_command(
        "docker exec lpr-backend curl -s -X POST http://localhost:8000/api/auth/login "
        "-H 'Content-Type: application/x-www-form-urlencoded' "
        "-d 'username=admin&password=admin123'"
    )
    print(out.read().decode())
    print(err.read().decode())

    # Check if users table has data
    print("=== DB Users ===")
    _, out, _ = ssh.exec_command(
        "docker exec lpr-postgres psql -U lpr_user -d lpr_db -c 'SELECT username, role, is_active FROM users;' 2>&1"
    )
    print(out.read().decode())
    
    ssh.close()

check_remote()
