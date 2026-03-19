# 🏥 MedClinic API

REST API для управления медицинской клиникой — пациенты, записи к врачу, рецепты, медицинские карты и документы.

## 🚀 Быстрый старт

```bash
git clone https://github.com/timderbak/vuln-app-idor-bac.git
cd vuln-app-idor-bac

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

База данных заполняется тестовыми данными при первом запуске.

## 📚 Документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Стек

- FastAPI 0.104
- SQLite + SQLAlchemy 2.0
- JWT + API Key аутентификация
- Python 3.9+

## 👥 Тестовые аккаунты

| Email | Пароль | Роль |
|-------|--------|------|
| `john@patient.com` | `patient123` | patient |
| `jane@patient.com` | `patient123` | patient |
| `mike@patient.com` | `patient123` | patient |
| `sarah@doctor.com` | `doctor123` | doctor |
| `james@doctor.com` | `doctor123` | doctor |
| `anna@nurse.com` | `nurse123` | nurse |
| `admin@clinic.com` | `admin123` | admin |

## 🔑 Аутентификация

```bash
# Получить токен
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@patient.com","password":"patient123"}'

# Использовать токен
curl http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer <токен>"
```

## 📁 Структура

```
app/
├── main.py              # Приложение FastAPI
├── auth.py              # Аутентификация
├── database.py          # БД
├── models.py            # Модели
├── seed.py              # Тестовые данные
└── routers/
    ├── auth_router.py   # Логин, регистрация
    ├── patients.py      # Пациенты
    ├── appointments.py  # Записи к врачу
    ├── prescriptions.py # Рецепты
    ├── medical_records.py # Медкарты
    ├── files.py         # Файлы
    └── admin.py         # Админка
```
