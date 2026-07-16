import paramiko

def diagnose_docker_networking():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    # 1. Find Gateway IP of the docker compose network
    print("=== DOCKER GATEWAYS ===")
    _, out, _ = ssh.exec_command("docker network inspect sunar_lpr_default | grep Gateway")
    print(out.read().decode())
    
    # 2. Test pinging localhost:8554 from backend using different host IPs
    ips_to_test = ["172.18.0.1", "172.17.0.1", "172.19.0.1"]
    for ip in ips_to_test:
        print(f"=== TESTING TCP CONNECTION TO {ip}:8554 FROM BACKEND ===")
        _, out, _ = ssh.exec_command(
            f"docker exec lpr-backend python -c 'import socket; s=socket.socket(); s.settimeout(2); s.connect((\"{ip}\", 8554)); print(\"BAGLANTI BASARILI\")' 2>&1"
        )
        print(out.read().decode())

    # 3. Check sshd_config GatewayPorts on the server
    print("=== SSHD GATEWAY PORTS CONFIG ===")
    _, out, _ = ssh.exec_command("grep -i GatewayPorts /etc/ssh/sshd_config")
    print(out.read().decode())

    ssh.close()

diagnose_docker_networking()
