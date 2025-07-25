#!/usr/bin/env python3
import os
import subprocess

# Update and upgrade system
subprocess.run(['sudo', 'apt', 'update'], check=True)
subprocess.run(['sudo', 'apt', 'upgrade', '-y'], check=True)

# Install dependencies
subprocess.run(['sudo', 'apt', 'install', '-y', 'build-essential', 'cmake', 'git'], check=True)

# Clone Stockfish
if not os.path.exists('Stockfish'):
    subprocess.run(['git', 'clone', 'https://github.com/official-stockfish/Stockfish.git'], check=True)

# Build Stockfish
os.chdir('Stockfish/src')
subprocess.run(['make', f'-j{os.cpu_count()}'], check=True)

# Move binary to system path
subprocess.run(['sudo', 'cp', 'stockfish', '/usr/local/bin/'], check=True)

# Create systemd service file
service_content = '''
[Unit]
Description=Stockfish Chess Engine
After=network.target

[Service]
ExecStart=/usr/local/bin/stockfish
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
'''

with open('/tmp/stockfish.service', 'w') as f:
    f.write(service_content)

# Move service file and enable service
subprocess.run(['sudo', 'mv', '/tmp/stockfish.service', '/etc/systemd/system/stockfish.service'], check=True)
subprocess.run(['sudo', 'systemctl', 'daemon-reexec'], check=True)
subprocess.run(['sudo', 'systemctl', 'enable', 'stockfish'], check=True)
subprocess.run(['sudo', 'systemctl', 'start', 'stockfish'], check=True)

print("Stockfish installation and setup complete.")