from utils import *

def main():
    if len(sys.argv) != 2:
        print("Usage: python psg.py <server1,server2>")
        sys.exit(1)
    
    servers = parse_servers(sys.argv[1])
    if len(servers) < 2:
        print("Please provide at least 2 servers separated by comma")
        sys.exit(1)

    least_loaded = None
    min_load = float('inf')
    ssh_clients = {}
    
    key = paramiko.RSAKey.from_private_key_file("private_key")
    
    for server in servers:
        try:
            print(f"Connecting to {server}...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=server, username='root', pkey=key)
            
            os_type = detect_os(ssh)
            load = get_server_load(ssh)
            print(f"Server {server} ({os_type}) load: {load}")
            
            ssh_clients[server] = (ssh, os_type)
            
            if load < min_load:
                min_load = load
                least_loaded = server
        except Exception as e:
            print(f"Error connecting to {server}: {e}")
            continue
    
    if not least_loaded:
        print("Could not connect to any server")
        sys.exit(1)
    
    target_server, second_server = least_loaded, servers[0] if servers[0] != least_loaded else servers[1]
    ssh, os_type = ssh_clients[target_server]
    
    print(f"Selected server: {target_server} (load: {min_load})")
    
    try:
        print("Installing PostgreSQL...")
        install_postgresql(ssh, os_type)
        
        print("Configuring PostgreSQL...")
        configure_postgresql(ssh, os_type, second_server)
        
        print("Testing PostgreSQL...")
        if test_postgresql(target_server):
            print("PostgreSQL installed and configured successfully!")
            print(f"User 'student' can connect only from {second_server}")
            print(f"Test query 'SELECT 1' executed successfully")
        else:
            print("PostgreSQL installation completed but test failed")
    except Exception as e:
        print(f"Error during installation: {e}")
        sys.exit(1)
    finally:
        for ssh, _ in ssh_clients.values():
            ssh.close()

if __name__ == "__main__":
    main()