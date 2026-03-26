# API Handlowe

Backend API dla aplikacji projektów handlowych oparty o **FastAPI** i **PostgreSQL**.  
API obsługuje projekty, słowniki, relacje projektowe oraz odczyt danych z widoków CRM/ERP.

## Technologie

- Python
- FastAPI
- PostgreSQL
- Docker
- Uvicorn

## Struktura projektu

```text
API-handlowe/
├─ app/
│  ├─ main.py
│  ├─ database.py
│  ├─ config.py
│  ├─ routers/
│  ├─ schemas/
│  └─ utils/
├─ .env
├─ .env.example
├─ .dockerignore
├─ .gitignore
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
└─ README.md
```

## Wymagania
Lokalnie
Python 3.11+ lub 3.12
dostęp do bazy PostgreSQL
plik .env z konfiguracją

Docker
Docker Desktop
Docker Compose

Konfiguracja .env

Utwórz plik .env w katalogu głównym projektu.
Przykład:
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=twoja_baza
DB_USER=twoj_user
DB_PASSWORD=twoje_haslo

Uruchomienie lokalne

Instalacja zależności
python -m pip install -r requirements.txt
Start aplikacji
python -m uvicorn app.main:app --reload
Adresy lokalne
API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs
Health check: http://127.0.0.1:8000/health

Uruchomienie w Dockerze
Build i start
docker compose up --build
Start w tle
docker compose up --build -d
Zatrzymanie
docker compose down
Logi
docker compose logs -f
Adresy Docker
API: http://127.0.0.1:4008
Swagger: http://127.0.0.1:4008/docs
Health check: http://127.0.0.1:4008/health

## Główne endpointy
Projekty
GET /projects
GET /projects/{id}
GET /projects/{id}/full
POST /projects
PUT /projects/{id}
PATCH /projects/{id}/archive
PATCH /projects/{id}/unarchive
Lista projektów

Obsługuje:

filtrowanie
paginację
sortowanie

Przykład:

/projects?search=PH/2026&owner_user_id=48180&is_archived=false&limit=20&offset=0&sort_by=created_at&sort_dir=desc
Statystyki i moje projekty
GET /projects/stats
GET /projects/my
Słowniki
GET /project-statuses
GET /project-stages
GET /project-types
Użytkownicy i taski z CRM
GET /users
GET /tasks
Widoki ERP
GET /erp/kntkarty
GET /erp/kntosoby
GET /erp/tranag
GET /erp/zamnag
Relacje projektu
GET /project-task-links
POST /project-task-links
DELETE /project-task-links/{id}
GET /project-team
POST /project-team
DELETE /project-team/{id}
GET /project-erp-links
POST /project-erp-links
DELETE /project-erp-links/{id}
Historia etapu
GET /project-stage-history
Główne zasady biznesowe
zapis wykonywany jest wyłącznie do schematu handlowe
dane z crm są tylko do odczytu
zmiana etapu projektu zapisuje się automatycznie do project_stage_history
archiwizacja projektu odbywa się przez PATCH
walidowane są m.in.:
owner_user_id
created_by
updated_by
status_id
stage_id
project_type_id
unikalność project_number
Walidacje biznesowe
dla otwartego etapu actual_close_date musi być puste
dla zamkniętego etapu actual_close_date jest wymagane
etap oznaczony jako wygrany lub przegrany musi być etapem zamkniętym
Testowanie

Najwygodniej testować API przez Swagger:

lokalnie: http://127.0.0.1:8000/docs
Docker: http://127.0.0.1:4008/docs
Wdrożenie na serwer

Docelowo aplikacja może zostać uruchomiona na serwerze przez Docker.

Do wdrożenia potrzebne będą:

dostęp do serwera
Docker / Docker Compose
plik .env
otwarty port dla API
możliwość komunikacji z PostgreSQL
Uwagi
nie commitować pliku .env
dane dostępowe do bazy trzymać poza repozytorium
przed wdrożeniem sprawdzić dostępność portu i połączenie z bazą