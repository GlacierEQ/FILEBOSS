#!/bin/bash

# Update and install packages
sudo apt-get update
sudo apt-get install -y python3.12 python3-pip python3.12-venv nginx supervisor

# Create a virtual environment
python3.12 -m venv /home/ubuntu/app/venv

# Configure Nginx
sudo tee /etc/nginx/sites-available/fileboss <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/fileboss /etc/nginx/sites-enabled
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# Configure Supervisor
sudo tee /etc/supervisor/conf.d/fileboss.conf <<EOF
[program:fileboss]
command=/home/ubuntu/app/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
directory=/home/ubuntu/app
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/fileboss.err.log
stdout_logfile=/var/log/fileboss.out.log
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fileboss
