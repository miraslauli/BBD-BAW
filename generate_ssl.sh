#!/bin/bash

# Tworzenie certyfikatu SSL dla środowiska deweloperskiego
echo "Tworzenie certyfikatu SSL z podpisem własnym..."

# Tworzymy katalog dla certyfikatów
mkdir -p ssl

# Generujemy klucz prywatny
openssl genrsa -out ssl/key.pem 2048

# Generujemy certyfikat
openssl req -new -x509 -key ssl/key.pem -out ssl/cert.pem -days 365 -subj "/C=BY/ST=Minsk/L=Minsk/O=University/OU=IT/CN=localhost"

# Ustawiamy uprawnienia dostępu
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

echo "Certyfikat SSL został utworzony w katalogu ssl/"
echo "Certyfikat: ssl/cert.pem"
echo "Klucz prywatny: ssl/key.pem"
echo ""
echo "UWAGA: To jest certyfikat z podpisem własnym do celów deweloperskich!"
echo "W środowisku produkcyjnym użyj certyfikatu od zaufanego CA (np. Let's Encrypt)" 