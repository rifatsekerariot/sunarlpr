import paramiko

def clean_mock_data():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15, banner_timeout=15)

    # Delete all access_logs (geçiş kayıtları - simulated detections)
    # Delete all vehicles except admin-created ones (all are mock)
    # Keep: admin user, default camera
    commands = [
        "docker exec lpr-postgres psql -U lpr_user -d lpr_db -c 'DELETE FROM access_logs;'",
        "docker exec lpr-postgres psql -U lpr_user -d lpr_db -c 'DELETE FROM vehicles;'",
        "docker exec lpr-postgres psql -U lpr_user -d lpr_db -c 'SELECT COUNT(*) as access_logs FROM access_logs;'",
        "docker exec lpr-postgres psql -U lpr_user -d lpr_db -c 'SELECT COUNT(*) as vehicles FROM vehicles;'",
        "docker exec lpr-postgres psql -U lpr_user -d lpr_db -c 'SELECT username, role FROM users;'",
        "docker exec lpr-postgres psql -U lpr_user -d lpr_db -c 'SELECT name, location FROM cameras;'",
    ]

    for cmd in commands:
        _, out, err = ssh.exec_command(cmd)
        result = out.read().decode().strip()
        error = err.read().decode().strip()
        print(f"CMD: {cmd[-60:]}")
        if result:
            print(f"  OUT: {result}")
        if error:
            print(f"  ERR: {error}")

    ssh.close()
    print("\nMock data temizlendi.")

clean_mock_data()
