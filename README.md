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
git clone [URL_REPOZYTORIUM]
cd [NAZWA_PROJEKTU]
```

### 2. Uruchomienie z użyciem Docker Compose
```bash
docker-compose up -d
```

## Testowanie API

### 1. Inicjalizacja danych testowych
```bash
# Tworzenie administratora
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin123!", "full_name": "Admin User", "is_admin": true}'

# Logowanie jako administrator
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin123!"}'
```

### 2. Zarządzanie produktami (wymaga tokenu administratora)
```bash
# Dodawanie nowego produktu
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer [TOKEN_ADMINA]" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "price": 99.99, "description": "Test Description"}'

# Pobieranie listy produktów
curl -X GET http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer [TOKEN_ADMINA]"
```

### 3. Rejestracja i logowanie użytkownika
```bash
# Rejestracja użytkownika
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!", "full_name": "Test User"}'

# Logowanie
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!"}'

# Zapisz token z odpowiedzi - będzie potrzebny do kolejnych operacji
```

### 4. Zarządzanie koszykiem (wymaga tokenu użytkownika)
```bash
# Dodawanie produktu do koszyka
curl -X POST http://localhost:8000/api/v1/cart/items \
  -H "Authorization: Bearer [TOKEN_UŻYTKOWNIKA]" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# Pobieranie zawartości koszyka
curl -X GET http://localhost:8000/api/v1/cart \
  -H "Authorization: Bearer [TOKEN_UŻYTKOWNIKA]"
```

### 5. Statystyki (wymaga tokenu administratora)
```bash
# Pobieranie statystyk sprzedaży
curl -X GET http://localhost:8000/api/v1/statistics/sales \
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