# claro_project/settings.py
import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
import dj_database_url

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === .env ===
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
    "core",          # <— agregado (permisos/reutilizables)
    "usuarios",
    "asignaciones",
    "auditoria",
]

AUTH_USER_MODEL = "usuarios.Usuario"

# === Middleware (CORS antes de CommonMiddleware) ===
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "corsheaders.middleware.CorsMiddleware",
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
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = False

# === URLS / WSGI ===
ROOT_URLCONF = "claro_project.urls"
WSGI_APPLICATION = "claro_project.wsgi.application"

# === Templates ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,
        ssl_require=True,   # necesario en Supabase
    )
}
# Si quieres usar un esquema propio más adelante:
# DATABASES["default"].setdefault("OPTIONS", {})
# DATABASES["default"]["OPTIONS"]["options"] = "-c search_path=db_claro,public"

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

# === JWT (SimpleJWT) ===
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# === Cookies para JWT HttpOnly ===
JWT_AUTH_COOKIE = "access"
JWT_AUTH_REFRESH_COOKIE = "refresh"
JWT_COOKIE_SAMESITE = "Lax"    # en prod: "None" + SECURE=True si hay dom. distintos
JWT_COOKIE_SECURE = False      # en prod: True
JWT_COOKIE_PATH = "/"
JWT_COOKIE_DOMAIN = None

# === DRF ===
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "usuarios.auth_cookie.CookieJWTAuthentication",  # cookie JWT
        "rest_framework_simplejwt.authentication.JWTAuthentication",  # Authorization: Bearer
        "rest_framework.authentication.SessionAuthentication",        # admin y Browsable API
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
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
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
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# === Backends de autenticación (email o “local-part”) ===
AUTHENTICATION_BACKENDS = [
    "usuarios.backends.EmailOrLocalBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# === Límites de subida ===
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
# Redirecciones post login/logout (para /api-auth/login/)
# LOGIN_REDIRECT_URL = "/docs/"           # o "/api/" si prefieres
LOGIN_REDIRECT_URL = "/api/"           # o "/api/" si prefieres
LOGOUT_REDIRECT_URL = "/api-auth/login/"
LOGIN_URL = "/api-auth/login/"