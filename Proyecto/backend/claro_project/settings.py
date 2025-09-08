# claro_project/settings.py
import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
import dj_database_url

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === .env ===
# Coloca en backend/.env:
# DATABASE_URL=postgresql://postgres:...@db.<project-ref>.supabase.co:5432/postgres?sslmode=require
load_dotenv(BASE_DIR / ".env")

# === Básico ===
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-key")  # cambia en prod
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# === Apps ===
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceros
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",

    # Apps del proyecto
    "usuarios",
    "asignaciones",
    "auditoria",
]

AUTH_USER_MODEL = "usuarios.Usuario"

# === Middleware (CORS antes de CommonMiddleware) ===
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "corsheaders.middleware.CorsMiddleware",  # <- primero para CORS
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# === CORS/CSRF (front en 5173/3000) ===
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# Cookies de CSRF (dev)
CSRF_COOKIE_SAMESITE = "Lax"   # mismo "site" (127.0.0.1) entre puertos es same-site
CSRF_COOKIE_SECURE = False     # en prod: True (HTTPS)

# === URLS / WSGI ===
ROOT_URLCONF = "claro_project.urls"
WSGI_APPLICATION = "claro_project.wsgi.application"

# === Templates (requerido por admin) ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # si luego usas templates propios: [BASE_DIR / "templates"]
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# === Base de datos ===
DATABASE_URL = os.environ.get("DATABASE_URL")  # viene del .env si estás con Supabase
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    # Fallback local (tu Postgres local)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "db_claro",
            "USER": "claro_user",
            "PASSWORD": "Claro_2025_pg",
            "HOST": "127.0.0.1",
            "PORT": "5432",
            "OPTIONS": {"sslmode": "prefer"},
        }
    }

# === Password validators ===
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === i18n ===
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# === Static & Media ===
STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# === JWT (SimpleJWT): access corto, refresh largo ===
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# === Cookies para JWT (autenticación vía cookie HttpOnly) ===
# Para dev, como front y back están en http://127.0.0.1 (puertos distintos), "site" es el mismo.
JWT_AUTH_COOKIE = "access"        # nombre cookie access
JWT_AUTH_REFRESH_COOKIE = "refresh"
JWT_COOKIE_SAMESITE = "Lax"       # en prod con dominios distintos: "None" + SECURE=True
JWT_COOKIE_SECURE = False         # en prod: True (HTTPS)
JWT_COOKIE_PATH = "/"
JWT_COOKIE_DOMAIN = None          # en prod: tu dominio, ej ".midominio.com"

# === DRF ===
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # 1) Lee JWT desde cookie HttpOnly (usuarios/auth_cookie.py)
        "usuarios.auth_cookie.CookieJWTAuthentication",
        # 2) Soporta Authorization: Bearer ...
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # 3) Sesión (útil para /admin y browsable API)
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ),
    # Paginación
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,

    # OpenAPI/Swagger con drf-spectacular
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# === drf-spectacular (OpenAPI) ===
SPECTACULAR_SETTINGS = {
    "TITLE": "ClaroVTR API",
    "DESCRIPTION": "API para asignaciones y auditorías",
    "VERSION": "1.0.0",
}

# === Hash de contraseñas (bcrypt primero) ===
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",  # compat
]

# === Backends de autenticación (email o “local-part”) ===
AUTHENTICATION_BACKENDS = [
    "usuarios.backends.EmailOrLocalBackend",     # backend custom
    "django.contrib.auth.backends.ModelBackend", # fallback
]

# === Límites de subida ===
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB por request
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB por archivo
