#!/bin/sh

echo "Checking environment variables ..."
if [ -z "$MYDOMAIN" ]; then
  echo "ERROR: MYDOMAIN is not set."
  exit 1
fi
if [ -z "$REDIRECTDOMAIN" ]; then
  echo "ERROR: REDIRECTDOMAIN is not set."
  exit 1
fi
if [ -z "$REALITYCLIENTS" ]; then
  echo "ERROR: REALITYCLIENTS is not set."
  exit 1
fi
if [ -z "$GRPCCLIENTS" ]; then
  echo "ERROR: GRPCCLIENTS is not set."
  exit 1
fi
if [ -z "$REALITYPRIVATEKEY" ]; then
  echo "ERROR: REALITYPRIVATEKEY is not set."
  exit 1
fi
echo "MYDOMAIN: $MYDOMAIN"
echo "REDIRECTDOMAIN: $REDIRECTDOMAIN"
echo "SERVERIP: $SERVERIP"
echo "SERVERPORT: $SERVERPORT"
echo "REALITYCLIENTS: $REALITYCLIENTS"
echo "REALITYPRIVATEKEY: $REALITYPRIVATEKEY"
echo "REALITYSHOW: $REALITYSHOW"
echo "REALITYMINCLIENTVER: $REALITYMINCLIENTVER"
echo "REALITYMAXCLIENTVER: $REALITYMAXCLIENTVER"
echo "REALITYMAXTIMEDIFF: $REALITYMAXTIMEDIFF"
echo "REALITYSHORTIDS: $REALITYSHORTIDS"
echo "GRPCCLIENTS: $GRPCCLIENTS"
echo "GRPCCLIENTS: $GRPCSERVICE"
echo "EMAIL: $EMAIL"
echo

echo "Encoding arrays ..."
comma_required=false
REALITYCLIENTS=$(echo "$REALITYCLIENTS" | tr -d ' ')
REALITYCLIENT_ARRAY=`echo $REALITYCLIENTS | tr ',' '\n'`
while IFS= read -r client; do
  if $comma_required ; then
    builtArray="${builtArray},"
  fi
  inside_brackets=$(echo "$client" | awk -F'[][]' '{print $2}')
  prefix=$(echo "$client" | awk -F'[' '{print $1}')
  if [ -z "$inside_brackets" ]; then
    thisClient="{\"id\":\"$client\"}"
  else
    thisClient="{\"id\":\"$prefix\",\"flow\":\""$inside_brackets"\"}"
  fi
  builtArray="${builtArray}${thisClient}"
  comma_required=true;
done <<-EOF
$REALITYCLIENT_ARRAY
EOF
REALITYCLIENTS="${builtArray}"
echo "REALITYCLIENTS: $REALITYCLIENTS"

if [ -z "$REALITYSHORTIDS" ]; then
  REALITYSHORTIDS="\"\""
else
  builtArray=
  comma_required=false
  REALITYSHORTIDS=$(echo "$REALITYSHORTIDS" | tr -d ' ')
  REALITYSHORTID_ARRAY=`echo $REALITYSHORTIDS | tr ',' '\n'`
  while IFS= read -r shortid; do
    if $comma_required ; then
      builtArray="${builtArray},"
    fi
    builtArray="${builtArray}\"${shortid}\""
    comma_required=true
  done <<-EOF
$REALITYSHORTID_ARRAY
EOF
  REALITYSHORTIDS="${builtArray}"
fi
echo "REALITYSHORTIDS: $REALITYSHORTIDS"

builtArray=
comma_required=false
GRPCCLIENTS=$(echo "$GRPCCLIENTS" | tr -d ' ')
GRPCCLIENT_ARRAY=`echo $GRPCCLIENTS | tr ',' '\n'`
while IFS= read -r client; do
  if $comma_required ; then
    builtArray="${builtArray},"
  fi
  thisClient="{\"id\":\"$client\"}"
  builtArray="${builtArray}${thisClient}"
  comma_required=true
done <<-EOF
$GRPCCLIENT_ARRAY
EOF
GRPCCLIENTS="${builtArray}"
echo "GRPCCLIENTS: $GRPCCLIENTS"
echo

echo "Preparing nginx for http ..."
mkdir -p /website
mkdir -p /etc/nginx/conf.d
sed "s/<REDIRECTDOMAIN>/$REDIRECTDOMAIN/g" /index.html.template > /website/index.html
echo "Website index:"
cat /website/index.html
echo
sed "s/<MYDOMAIN>/$MYDOMAIN/g" /nginx-80.conf.template | \
sed "s/<REDIRECTDOMAIN>/$REDIRECTDOMAIN/g" > /etc/nginx/conf.d/nginx-80.conf
echo "Nginx for http:"
cat /etc/nginx/conf.d/nginx-80.conf
echo
if [ -f "/etc/nginx/conf.d/nginx-ssl.conf" ] ; then rm /etc/nginx/conf.d/nginx-ssl.conf; fi
/usr/sbin/nginx

echo "Preparing acme.sh ..."
if [ ! -f "/root/.acme.sh/acme.sh" ] ; then
  echo "Installing acme.sh ..."
  temp_cron_file=$(mktemp)
  crontab -u root "$temp_cron_file"
  rm -f "$temp_cron_file"
  curl https://get.acme.sh | sh
fi
if [ ! -f "/root/.acme.sh/acme.sh" ] ; then
  echo "Failed to install acme.sh!"
  exit 2
fi
PATH="/root/.acme.sh/:$PATH"
acme.sh --upgrade --auto-upgrade
acme.sh --set-default-ca --server letsencrypt
acme.sh --update-account --register-account
acme.sh --update-account --accountemail $EMAIL

echo "Checking certificates ..."
mkdir -p /cert
mkdir -p /cert/$MYDOMAIN
if [ ! -f "/cert/$MYDOMAIN/fullchain.pem" ] || [ ! -f "/cert/$MYDOMAIN/key.pem" ]; then
  echo "Issuing certificate ..."
  acme.sh --issue -d $MYDOMAIN --webroot /website
fi

echo "Getting certificates ..."
acme.sh --install-cert -d $MYDOMAIN --key-file /cert/$MYDOMAIN/key.pem --fullchain-file /cert/$MYDOMAIN/fullchain.pem --reloadcmd "/usr/sbin/nginx -s reload"

echo "Preparing nginx for https ..."
sed "s/<MYDOMAIN>/$MYDOMAIN/g" /nginx-ssl.conf.template | \
sed "s|<REDIRECTDOMAIN>|$REDIRECTDOMAIN|g" | \
sed "s|<GRPCSERVICE>|$GRPCSERVICE|g" > /etc/nginx/conf.d/nginx-ssl.conf
echo "Nginx for https:"
cat /etc/nginx/conf.d/nginx-ssl.conf
echo
echo "Reloading nginx ..."
/usr/sbin/nginx -s reload
echo 

echo "Preparing xray ..."
sed "s/<SERVERIP>/$SERVERIP/g" /xray.conf.template | \
sed "s/<SERVERPORT>/$SERVERPORT/g" | \
sed "s/<REALITYCLIENTS>/$REALITYCLIENTS/g" | \
sed "s/<REALITYSHOW>/$REALITYSHOW/g" | \
sed "s/<MYDOMAIN>/$MYDOMAIN/g" | \
sed "s|<REALITYPRIVATEKEY>|$REALITYPRIVATEKEY|g" | \
sed "s/<REALITYMINCLIENTVER>/$REALITYMINCLIENTVER/g" | \
sed "s/<REALITYMAXCLIENTVER>/$REALITYMAXCLIENTVER/g" | \
sed "s/<REALITYMAXTIMEDIFF>/$REALITYMAXTIMEDIFF/g" | \
sed "s/<REALITYSHORTIDS>/$REALITYSHORTIDS/g" | \
sed "s/<GRPCCLIENTS>/$GRPCCLIENTS/g" | \
sed "s|<GRPCSERVICE>|$GRPCSERVICE|g" > /etc/xray/config.json
echo "Xray config:"
cat /etc/xray/config.json
echo
echo "Staring xray ..."
/usr/bin/xray -config /etc/xray/config.json
