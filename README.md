# System E-commerce - Projekt na zaliczenie

## Student
Miraslau Chyhir

## Przedmioty
- Bezpieczeństwo baz danych
- Bezpieczeństwo aplikacji webowych

## Stos technologiczny
- **Backend**: FastAPI (Python 3.11+)
- **Baza danych**: SQLite
- **Autentykacja**: JWT (JSON Web Tokens)
- **HTTPS**: Certyfikat SSL/TLS
- **Konteneryzacja**: Docker i Docker Compose
- **Backup**: Automatyczne kopie zapasowe bazy danych

## Wymagania systemowe
- Docker i Docker Compose
- Python 3.11+

## Instalacja i uruchomienie

### 1. Sklonuj repozytorium
```bash
git clone https://github.com/miraslauli/BBD-BAW.git
cd BBD-BAW
```

### 2. Uruchomienie z użyciem Docker Compose
```bash
docker-compose up -d
```

## Testowanie API

### 1. Operacje na bazie danych
```bash
# Inicjalizacja bazy danych
curl -X POST "http://localhost:8000/database/init"

# Tworzenie danych testowych
curl -X POST "http://localhost:8000/database/sample-data"

# Wykonanie kopii zapasowej bazy danych
curl -X POST "http://localhost:8000/database/backup"

# Przywrócenie bazy danych z kopii zapasowej
curl -X POST "http://localhost:8000/database/restore" \
  -H "Content-Type: application/json" \
  -d '{"backup_path": "backup_2024_03_21.sqlite"}'

# Wykonanie zrzutu SQL
curl -X POST "http://localhost:8000/database/dump"

# Testowanie indeksów
curl -X GET "http://localhost:8000/database/test-indexes"

# Demonstracja operacji CRUD
curl -X GET "http://localhost:8000/database/crud-demo"
```

### 2. Inicjalizacja danych testowych
```bash
# Tworzenie administratora
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin123!", "full_name": "Admin User", "is_admin": true}'

# Logowanie jako administrator
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin123!"}'

# Zapisz token z odpowiedzi powyższego zapytania - będzie potrzebny do kolejnych operacji
```

### 3. Zarządzanie produktami (wymaga tokenu administratora)
```bash
# Dodawanie nowego produktu
curl -X POST "http://localhost:8000/products/admin" \
  -H "Authorization: Bearer [TOKEN_ADMINA]" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "price": 99.99, "description": "Test Description", "stock_quantity": 100, "category_id": 1, "is_active": true}'

# Pobieranie listy produktów
curl -X GET "http://localhost:8000/products" \
  -H "Authorization: Bearer [TOKEN_ADMINA]"

# Dodawanie nowej kategorii
curl -X POST "http://localhost:8000/products/categories/admin" \
  -H "Authorization: Bearer [TOKEN_ADMINA]" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Category", "description": "Test Category Description"}'
```

### 4. Rejestracja i logowanie użytkownika
```bash
# Rejestracja użytkownika
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!", "full_name": "Test User"}'

# Logowanie
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!"}'

# Zapisz token z odpowiedzi - będzie potrzebny do kolejnych operacji
```

### 5. Zarządzanie koszykiem (wymaga tokenu użytkownika)
```bash
# Dodawanie produktu do koszyka
curl -X POST "http://localhost:8000/cart/add" \
  -H "Authorization: Bearer [TOKEN_UŻYTKOWNIKA]" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# Pobieranie zawartości koszyka
curl -X GET "http://localhost:8000/cart" \
  -H "Authorization: Bearer [TOKEN_UŻYTKOWNIKA]"

# Aktualizacja ilości produktu w koszyku
curl -X PUT "http://localhost:8000/cart/items/1" \
  -H "Authorization: Bearer [TOKEN_UŻYTKOWNIKA]" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 3}'

# Usuwanie produktu z koszyka
curl -X DELETE "http://localhost:8000/cart/items/1" \
  -H "Authorization: Bearer [TOKEN_UŻYTKOWNIKA]"

# Czyszczenie koszyka
curl -X DELETE "http://localhost:8000/cart/clear" \
  -H "Authorization: Bearer [TOKEN_UŻYTKOWNIKA]" \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

### 6. Statystyki (wymaga tokenu administratora)
```bash
# Pobieranie statystyk bazy danych
curl -X GET "http://localhost:8000/database/statistics" \
  -H "Authorization: Bearer [TOKEN_ADMINA]"
```

## Elementy bezpieczeństwa

### 1. Bezpieczeństwo bazy danych
- Automatyczne kopie zapasowe co 24 godziny
- Indeksy na kluczowych kolumnach dla optymalizacji zapytań
- Wykonywanie zrzutów SQL przed każdą migracją
- Bezpieczne zapytania CRUD z walidacją danych

### 2. Bezpieczeństwo aplikacji
- Wymuszone HTTPS
- Walidacja wszystkich danych wejściowych
- Ochrona przed atakami typu SQL Injection
- Implementacja rate limitingu
- Bezpieczne przechowywanie haseł (bcrypt)
- Logowanie wszystkich operacji CRUD

## Logi i monitoring
- Dostęp do logów aplikacji: `docker-compose logs -f backend`

## Dokumentacja API
Pełna dokumentacja API dostępna jest pod adresem: `http://localhost:8000/docs` po uruchomieniu aplikacji.