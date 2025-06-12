# Elementy bezpieczeństwa systemu

## 🔒 Konfiguracja serwera WWW z HTTPS

### Ustawienia SSL/TLS:
- **Protokoły**: TLSv1.2, TLSv1.3 (wyłączone niebezpieczne wersje)
- **Szyfry**: ECDHE-RSA-AES256-GCM i inne nowoczesne algorytmy
- **HSTS**: Strict-Transport-Security с max-age=63072000
- **SSL Stapling**: Włączony dla wydajności

### Nagłówki bezpieczeństwa:
- `X-Frame-Options: SAMEORIGIN` - ochrona przed clickjacking
- `X-Content-Type-Options: nosniff` - zapobieganie MIME sniffing
- `X-XSS-Protection: 1; mode=block` - ochrona przed XSS
- `Referrer-Policy: strict-origin-when-cross-origin` - kontrola referrer
- `Content-Security-Policy` - polityka bezpieczeństwa zawartości

### Ograniczenia prędkości:
- **API endpoints**: 100 zapytań/minutę
- **Autoryzacja**: 5 zapytań/minutę  
- **Burst protection**: skonfigurowane do zapobiegania DDoS

### Ustawienia Nginx:
```nginx
# Ukrycie wersji serwera
server_tokens off;

# Ograniczenia rozmiaru zapytania
client_max_body_size 10M;

# Timeouty
client_body_timeout 10s;
client_header_timeout 10s;
keepalive_timeout 5s;

# Zabronienie dostępu do ukrytych plików
location ~ /\. {
    deny all;
}
```

## 🛡️ Elementy bezpieczeństwa baz danych

### 1. Kopia zapasowa i przywracanie
```python
# API endpointy:
POST /database/backup     # Tworzenie kopii zapasowej
POST /database/restore    # Przywracanie z kopii
```

**Bezpieczeństwo**:
- Tylko administratorzy mogą tworzyć i przywracać kopie zapasowe
- Pliki kopii zapasowych są przechowywane z ograniczonym dostępem
- Automatyczna kontrola integralności podczas przywracania

### 2. Indeksy na tabelach
```sql
-- Proste indeksy
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_products_category_id ON products(category_id);

-- Kompozytowe indeksy do optymalizacji
CREATE INDEX idx_user_email_active ON users(email, is_active);
CREATE INDEX idx_product_category_active ON products(category_id, is_active);
CREATE INDEX idx_product_price_range ON products(price, is_active);
CREATE INDEX idx_order_user_status ON orders(user_id, status);
CREATE INDEX idx_cart_user_product ON cart_items(user_id, product_id);
```

**Zalety**:
- Przyspieszanie wyszukiwania i filtracji danych
- Optymalizacja operacji JOIN
- Poprawa wydajności uwierzytelniania

### 3. SQL dumpy
```python
# API endpoint:
POST /database/dump       # Tworzenie SQL dumpu
```

**Cechy**:
- Pełny dump struktury i danych
- Użycie sqlite3.iterdump() do bezpieczeństwa
- Przechowywanie w formacie tekstowym do przenośności

### 4. Demonstracja operacji CRUD
```python
# API endpoint:
GET /database/crud-demo    # Demonstracja losowych operacji CRUD
```

**Operacje**:
- **CREATE**: Tworzenie nowych produktów z walidacją
- **READ**: Wyszukiwanie produktów według różnych kryteriów  
- **UPDATE**: Aktualizacja cen i pozostałości produktów
- **DELETE**: Usuwanie przestarzałych produktów

## 🔐 Uwierzytelnianie i autoryzacja

### JWT tokeny:
- **Access token**: 24 godziny
- **Refresh token**: 7 dni
- **Algorytm**: HS256
- **Tajny klucz**: 256-bitowy losowy klucz

### Haszowanie haseł:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

### Role użytkowników:
- **User**: zwykłi użytkownicy
- **Admin**: administratorzy z pełnymi uprawnieniami

## 🚨 Ochrona przed atakami

### 1. SQL Injection
- Użycie SQLAlchemy ORM
- Parametryzowane zapytania
- Walidacja danych wejściowych za pomocą Pydantic

### 2. XSS (Cross-Site Scripting)
- Nagłówek X-XSS-Protection
- Content Security Policy
- Automatyczne ekranowanie w Pydantic

### 3. CSRF (Cross-Site Request Forgery)
- SameSite cookies (planowane)
- CSRF tokeny (planowane)

### 4. DDoS i Brute Force
- Rate limiting przez Nginx
- Ograniczenia na autoryzację
- Monitorowanie podejrzanej aktywności

## 📊 Monitorowanie bezpieczeństwa

### Logowanie:
- Nginx access/error logs
- Audyt administracyjnych działań
- Monitorowanie nieudanych prób logowania

### Alerty:
```python
# API endpoint:
GET /stats/inventory/alerts  # Powiadomienia o stanie magazynu
```

## 🔧 Docker bezpieczeństwo

### Kontener Nginx:
```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - CHOWN
  - DAC_OVERRIDE
  - SETGID
  - SETUID
  - NET_BIND_SERVICE
```

### Izolacja sieciowa:
- Własna sieć Docker
- Izolowany subnet: 172.20.0.0/16
- Kontenery nie są dostępne z zewnątrz bez proxy

## 📝 Rekomendacje dla produkcji

1. **SSL certyfikat**: Użycie Let's Encrypt lub komercyjnego CA
2. **WAF**: Wdrożenie Web Application Firewall
3. **Monitorowanie**: Skonfigurowanie systemów monitorowania i alertowania
4. **Backup**: Automatyzacja tworzenia kopii zapasowych
5. **Updates**: Regularne aktualizowanie zależności i kontenerów
6. **Secrets**: Użycie zewnętrznych systemów zarządzania tajemnicami
7. **Network**: Skonfigurowanie firewall i VPN do administracji 