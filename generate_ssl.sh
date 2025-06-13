#!/bin/bash

# Tworzymy katalog dla certyfikatów
mkdir -p ssl

# Generujemy klucz prywatny
openssl genrsa -out ssl/key.pem 2048

# Generujemy certyfikat
openssl req -new -x509 -key ssl/key.pem -out ssl/cert.pem -days 365 -subj "/C=PL/ST=Warsaw/L=Warsaw/O=University/OU=IT/CN=localhost"

# Ustawiamy uprawnienia dostępu
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem