# claro_project/settings.py
import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
import dj_database_url

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# === Básico ===
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-key")  # cambia en prod
DEBUG = bool(int(os.environ.get("DEBUG", "1")))  # 1 en dev, 0 en prod
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")]

# Marca de entorno (para activar seguridad fuerte en PROD)
DJANGO_ENV = os.environ.get("DJANGO_ENV", "development").lower()
IS_PROD = (DJANGO_ENV in {"prod", "production"}) or (DEBUG is False)

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
    "core",
    "usuarios",
    "asignaciones",
    "auditoria",
]

AUTH_USER_MODEL = "usuarios.Usuario"

# === Middleware ===
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

# === CORS/CSRF (ajusta según tu front) ===
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS[:]
CORS_ALLOW_CREDENTIALS = True

# Cookies de CSRF (dev)
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = False  # en PROD lo forzamos True más abajo

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

# === Base de datos (Supabase / dj_database_url) ===
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,
        ssl_require=False,   # necesario en Supabase
    )
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

# === JWT (SimpleJWT) — configuración simple sin rotación/blacklist ===
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# === Cookies para JWT HttpOnly ===
JWT_AUTH_COOKIE = "access"
JWT_AUTH_REFRESH_COOKIE = "refresh"
JWT_COOKIE_SAMESITE = "Lax"    # en prod: "None" si hay front en otro dominio y HTTPS
JWT_COOKIE_SECURE = False      # en prod: True
JWT_COOKIE_PATH = "/"
JWT_COOKIE_DOMAIN = None

# === DRF ===
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "usuarios.auth_cookie.CookieJWTAuthentication",                        # cookie JWT
        "rest_framework_simplejwt.authentication.JWTAuthentication",           # Authorization: Bearer
        "rest_framework.authentication.SessionAuthentication",                 # admin y Browsable API
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
    "TITLE": "API ClaroVTR",
    "DESCRIPTION": "API para asignaciones, auditorías, historial y métricas",
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

LOGIN_REDIRECT_URL = "/api/"
LOGOUT_REDIRECT_URL = "/api-auth/login/"
LOGIN_URL = "/api-auth/login/"

# === Endurecer en PRODUCCIÓN, sin “ensuciar” dev ===
if IS_PROD:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    JWT_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    JWT_COOKIE_SECURE = False

# =========================================================
# === Email / Notificaciones (SMTP) — configuración única
# =========================================================
# Usa variables de entorno en .env; si falta algo, hay defaults seguros.
# Email (SMTP)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "0") == "1"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@localhost")

# Correos que reciben copia de todas las notificaciones
NOTIFY_ADMIN_EMAILS = [
    e.strip() for e in os.environ.get("NOTIFY_ADMIN_EMAILS", "").split(",") if e.strip()
]

# Forzar impresión a consola en dev (opcional)
if not IS_PROD and os.environ.get("EMAIL_CONSOLE", "0") == "1":
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
