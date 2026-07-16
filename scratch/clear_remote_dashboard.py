import paramiko

def clear_remote_dashboard_data():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== TRUNCATING ACCESS LOGS & VEHICLES ON REMOTE DATABASE (USERS INTACT) ===")
    sql_commands = (
        "docker exec -i lpr-postgres psql -U lpr_user -d lpr_db -c "
        "'TRUNCATE TABLE access_logs, vehicles RESTART IDENTITY CASCADE;'"
    )
    _, out, _ = ssh.exec_command(sql_commands)
    print(out.read().decode('utf-8'))
    
    ssh.close()

clear_remote_dashboard_data()
