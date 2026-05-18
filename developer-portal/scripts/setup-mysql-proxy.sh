#!/bin/bash
# Setup MySQL TCP proxy on DigitalOcean VPS
# Forwards port 13306 → AliCloud RDS MySQL (codatta-prod)

# Add SSH key
grep -q "beingzy@gmail.com" ~/.ssh/authorized_keys 2>/dev/null || echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCX2MIg6LiqtRfmF04hlhRh05zx0hwTEsU4pF61BvwKz2oLeSWgKpKjif+ZS0xLBJ5UMHW+YGAcibtJ08avpJzjm4SXogWv7QTnUyTPepo9DL4pX8ku6leXP/22j19e/tAP5rAT1WwZfgZGVxtaAo0BUFuu5CTxGsCVhDudPiNBmDZRi8WneWW855lWygTXxuJmYOZ+rOTrgHBtV8oAVIlND906LchPwWyu5UXUqTqMo6URJuscDxYNNIDrY8OJtWxXLB7IeVkirCC2/afTY+PNBFnPArpoP9XhN+096em3QU7FylP/sYuwWrQT+ekaGpBH7y4X8DlX8aYV1WB02SikiQ2nCMPQScxFpObGTbcAo40wNqbC/ODhcclGBB7yXAQaF1aRWprJQ0F00GKPGKGZXqTzuHgE46+m0g3j4HBGTlaEmmLiCS9XHWh5T67nUvtT0MZmtsiSZRTU7RBa7vXNTxhhyByNWf+CRH3dedyqgmouhmioZ1/T3aF4Y+Wzwk1QVobEKj7OoiwRmegwSmCgQvKP7+ouRE0Y2qkLbMU1x8/ylT8nfSc+MAUMZs2SZ0gfjt/aP9WtoB0XpB+hBfN7OxoluL9S3RpsjTJts5+++EgMFaKhbMVJakdCi++TzjvuYLvjki/BchWrLlApIuPRaExt6h3i32SPCuFQAF2Sfw== beingzy@gmail.com' >> ~/.ssh/authorized_keys

# Install socat if needed
which socat > /dev/null 2>&1 || apt install -y socat

# Write systemd service
cat <<'SVC' > /etc/systemd/system/mysql-proxy.service
[Unit]
Description=MySQL TCP Proxy to AliCloud RDS
After=network.target

[Service]
ExecStart=/usr/bin/socat TCP-LISTEN:13306,fork,reuseaddr TCP:codatta-prod.rwlb.singapore.rds.aliyuncs.com:3306
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVC

# Start service
systemctl daemon-reload
systemctl enable mysql-proxy
systemctl start mysql-proxy

# Verify
echo "=== STATUS ==="
systemctl is-active mysql-proxy
ss -tlnp | grep 13306
echo "=== DONE ==="
