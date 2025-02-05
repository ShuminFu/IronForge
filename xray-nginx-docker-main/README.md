# Environment

``DOMAIN``: Domain name. The tcp ports 80 and 443 of the created docker container should be accessible through the domain specified.

``XRAYIDS``: Id of the vless user in GUID, like ``d76abab0-fd53-4ad6-813b-7a3a1ec6afb1``. When multple ids required, separates them with commars, like ``ba1ee0e7-fc74-4596-9d68-169ee834248a,c7d7e6b2-eb7c-41e8-80f1-d6f881bb3746``.

``EMAIL``: Email address used while registering certificate using certbot. Default value is ``webadmin@cloudflare.com``.

``WSPATH``: WebSocket path. Default value is ``/cloud``.


Before docker started, ```DOMAIN``` and ```XRAYIDS``` must be set.

# Volume

To keep the certificates, mount a volume to ``/etc/letsencrypt``.
