# claro_project/settings.py
import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
import dj_database_url

# === Paths / .env ===
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")  # lee variables de entorno desde backend/.env

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
    # Blacklist/rotación para refresh tokens (seguridad sesiones largas)
    "rest_framework_simplejwt.token_blacklist",

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

# === CORS/CSRF (ajusta orígenes del front) ===
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS[:]  # simple
CORS_ALLOW_CREDENTIALS = True

# Cookies de CSRF (dev)
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = False  # en PROD se fuerza True más abajo

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

# === Base de datos (Supabase/Postgres) ===
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,
        ssl_require=True,  # necesario en Supabase
    )
}
# Si en el futuro usas un schema:
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

# === JWT (SimpleJWT) + cookies ===
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "AUTH_HEADER_TYPES": ("Bearer",),

    # Seguridad extra para sesiones largas:
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Cookies JWT (las gestiona usuarios/auth_views.py)
JWT_AUTH_COOKIE = "access"
JWT_AUTH_REFRESH_COOKIE = "refresh"
JWT_COOKIE_SAMESITE = "Lax"   # en producción puedes evaluar "Strict"
JWT_COOKIE_SECURE = False     # en PROD se fuerza True abajo
JWT_COOKIE_PATH = "/"
JWT_COOKIE_DOMAIN = None

# === DRF ===
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "usuarios.auth_cookie.CookieJWTAuthentication",                # JWT en cookie
        "rest_framework_simplejwt.authentication.JWTAuthentication",   # Authorization: Bearer
        "rest_framework.authentication.SessionAuthentication",         # admin & Browsable API
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
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
    # Si quieres que Swagger recuerde auth, descomenta:
    # "SWAGGER_UI_SETTINGS": {"persistAuthorization": True},
}

# === Hash de contraseñas (bcrypt primero) ===
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# === Backends de autenticación (email o local-part) ===
AUTHENTICATION_BACKENDS = [
    "usuarios.backends.EmailOrLocalBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# === Límites de subida ===
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# === Redirecciones post login/logout (para /api-auth/login/) ===
LOGIN_REDIRECT_URL = "/api/"
LOGOUT_REDIRECT_URL = "/api-auth/login/"
LOGIN_URL = "/api-auth/login/"

# === Seguridad fuerte en PRODUCCIÓN (no “ensucia” dev) ===
if IS_PROD:
    SECURE_SSL_REDIRECT = True             # obliga HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    JWT_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000         # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    # Si vas detrás de proxy/ingress:
    # SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
else:
    # DEV local cómodo
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    JWT_COOKIE_SECURE = False
