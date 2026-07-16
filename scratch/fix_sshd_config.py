import paramiko

def fix_sshd_config():
    host = '200.97.171.59'
    user = 'root'
    password = 'XgzF2A@LWmMhA-kQ'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=15)
    
    print("=== SSHD Konfigürasyonu Güncelleniyor ===")
    # Enable GatewayPorts yes to allow binding port forward to all interfaces (including docker bridge)
    commands = [
        "sed -i 's/#GatewayPorts no/GatewayPorts yes/g' /etc/ssh/sshd_config",
        "sed -i 's/GatewayPorts no/GatewayPorts yes/g' /etc/ssh/sshd_config",
        "grep -i GatewayPorts /etc/ssh/sshd_config",
        "systemctl restart ssh",
        "systemctl restart sshd || true"
    ]
    for cmd in commands:
        _, out, err = ssh.exec_command(cmd)
        print(f"CMD: {cmd} -> {out.read().decode().strip()} {err.read().decode().strip()}")
        
    ssh.close()

fix_sshd_config()
