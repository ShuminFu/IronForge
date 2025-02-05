#!/bin/bash

if [ -z "$DOMAIN" ]; then
  echo "ERROR: DOMAIN is not set"
  exit 1
fi

if [ -z "$XRAYIDS" ]; then
  echo "ERROR: DOMAIN is not set"
  exit 2
fi

# prepare html
mkdir -p /var/www/html
if [ ! -e "/var/www/html/index.html" ]; then cat <<EOF > /var/www/html/index.html
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"><head><meta http-equiv="refresh" content="0; url=https://www.cloudflare.com/" /></head><body>Redirecting...</body></html>
EOF
fi

# prepare 80 version of nginx for getting cert if no cert found
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] || [ ! -f "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ]; then
  cat <<EOF > /etc/nginx/conf.d/xray.conf
server {
    server_name $DOMAIN;
    error_page 400 = "https://www.cloudflare.com/";
    listen 80;
    root /var/www/html;
    index index.html index.htm;
    charset utf-8;
    if (\$request_method !~ ^(POST|GET)\$) {
        return  444;
    }
}
EOF
  /usr/sbin/nginx
  /usr/bin/certbot --nginx --non-interactive --agree-tos --email $EMAIL --redirect --expand --keep -d $DOMAIN
  /usr/sbin/nginx -s stop
fi

# prepare 443 version of nginx
cat <<EOF > /etc/nginx/conf.d/xray.conf
upstream vless {
    server 127.0.0.1:10086;
    keepalive 2176;
}
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    '' close;
}
server {
    server_name $DOMAIN;
    error_page 400 = "https://www.cloudflare.com/";
    listen 80;
    root /var/www/html;
    index index.html index.htm;
    charset utf-8;
    if (\$request_method !~ ^(POST|GET)\$) {
        return  444;
    }
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options nosniff;
    add_header Strict-Transport-Security max-age=15 always;
    resolver 8.8.8.8 valid=300s;
    location $WSPATH {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_requests 25600;
        keepalive_timeout 300 300;
        proxy_buffering off;
        proxy_buffer_size 8k;
        proxy_intercept_errors on;
        proxy_pass http://vless;
      }
      listen 443 ssl http2 backlog=1024 so_keepalive=120s:60s:10 reuseport;
      ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
      include /etc/letsencrypt/options-ssl-nginx.conf;
      ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
EOF
/usr/sbin/nginx
echo "30 2,14 * * * certbot renew --quiet" > /etc/crontab
chmod 0644 /etc/crontab
/usr/sbin/cron

# prepare xray
IFS=',' read -r -a values <<< "$XRAYIDS"
comma_required=false
for value in "${values[@]}"; do
  if $comma_required ; then
    json_output+=","
  fi
  json_output+="{\"id\":\"$value\",\"level\":0}";
  comma_required=true;
done
mkdir -p /etc/xray
cat <<EOF > /etc/xray/config.json
{
  "log": {
    "access": "",
    "loglevel": "warning",
    "error": ""
  },
  "inbounds": [
    {
      "port": 10086,
      "listen": "127.0.0.1",
      "tag": "v2-in",
      "protocol": "vless",
      "settings": {
        "clients": [$json_output],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {
          "path": "$WSPATH",
          "headers": { }
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "settings": { },
      "tag": "direct"
    },
    {
      "protocol": "blackhole",
      "settings": { },
      "tag": "blocked"
    }
  ],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {
        "type": "field",
        "inboundTag": [ "v2-in" ],
        "outboundTag": "direct"
      }
    ]
  }
}
EOF

/usr/bin/xray -config /etc/xray/config.json
