import sys
import paramiko
import time
import re
from typing import Tuple, List, Optional
import psycopg2
from psycopg2 import OperationalError


def parse_servers(input_str: str) -> List[str]:
    return [s.strip() for s in input_str.split(',') if s.strip()]

def get_server_load(ssh: paramiko.SSHClient) -> float:
    stdin, stdout, stderr = ssh.exec_command('uptime')
    output = stdout.read().decode().strip()
    match = re.search(r'load average:.*?(\d+\.\d+)', output)
    if match:
        return float(match.group(1))
    return 100.0

def install_postgresql(ssh: paramiko.SSHClient, os_type: str):
    if os_type == 'debian':
        commands = [
            'apt-get update',
            'apt-get install -y postgresql postgresql-contrib',
            'systemctl start postgresql',
            'systemctl enable postgresql'
        ]
    else:
        commands = [
            'yum install -y postgresql-server postgresql-contrib',
            'postgresql-setup --initdb',
            'systemctl start postgresql',
            'systemctl enable postgresql'
        ]
    
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode().strip()
            raise Exception(f"Command failed: {cmd}\nError: {error}")
        
def detect_os(ssh: paramiko.SSHClient) -> str:
    stdin, stdout, stderr = ssh.exec_command('cat /etc/os-release')
    output = stdout.read().decode().lower()
    if 'debian' in output:
        return 'debian'
    elif 'centos' in output or 'almalinux' in output:
        return 'centos'
    raise Exception("Unsupported OS")

def configure_postgresql(ssh: paramiko.SSHClient, os_type: str, second_server_ip: str):
    if os_type == 'debian':
        pg_dir = '/etc/postgresql/*/main/'
    else:
        pg_dir = '/var/lib/pgsql/data/'

    stdin, stdout, stderr = ssh.exec_command(f'ls -d {pg_dir}')
    pg_data_dir = stdout.read().decode().strip()

    hba_conf = f"{pg_data_dir}/pg_hba.conf"
    pg_conf = f"{pg_data_dir}/postgresql.conf"

    ssh.exec_command(f"echo \"host all all 0.0.0.0/0 md5\" >> {hba_conf}")

    ssh.exec_command(f"echo \"host all student {second_server_ip}/32 md5\" >> {hba_conf}")

    ssh.exec_command(f"echo \"listen_addresses = '*'\" >> {pg_conf}")

    ssh.exec_command('systemctl restart postgresql')

    create_user_commands = [
        "sudo -u postgres psql -c \"CREATE USER student WITH PASSWORD 'student';\"",
        "sudo -u postgres psql -c \"ALTER USER student CREATEDB;\"",
        "sudo -u postgres psql -c \"CREATE DATABASE student_db OWNER student;\""
    ]
    
    for cmd in create_user_commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode().strip()
            print(f"Warning: {error}")

def test_postgresql(host: str) -> bool:
    try:
        conn = psycopg2.connect(
            dbname="student_db",
            user="student",
            password="student",
            host=host,
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        return result == (1,)
    except OperationalError as e:
        print(f"PostgreSQL test failed: {e}")
        return False