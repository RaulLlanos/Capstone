# Proyecto/backend/claro_project/settings.py
from pathlib import Path
import os
from urllib.parse import urlparse, parse_qs
from datetime import timedelta
from dotenv import load_dotenv

# ——— Paths ———
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ——— Helpers env ———
def env(key: str, default: str = "") -> str:
    return os.getenv(key, default)

def env_bool(key: str, default: bool = False) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}

def env_list(key: str, default: str = "") -> list[str]:
    raw = os.getenv(key, default)
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]

# ——— Seguridad / Debug ———
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-unsafe-change-me")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")

# ——— Apps ———
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
    "rest_framework.authtoken",
    "drf_spectacular",
    "corsheaders",
    "django_filters",

    # Locales
    "core",
    "usuarios",
    "asignaciones",
    "auditoria",
]

AUTH_USER_MODEL = "usuarios.Usuario"

# ——— Middleware ———
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # CORS arriba
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Deja este si existe; si no, quítalo.
    "core.middleware.RoleAuthorizationMiddleware",
]

ROOT_URLCONF = "claro_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "claro_project.wsgi.application"

# ——— Base de datos ———
def db_from_url(url: str):
    if not url:
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
    parsed = urlparse(url)
    engine = {
        "postgres": "django.db.backends.postgresql",
        "postgresql": "django.db.backends.postgresql",
        "pgsql": "django.db.backends.postgresql",
    }.get(parsed.scheme, "django.db.backends.postgresql")

    q = parse_qs(parsed.query or "")
    sslmode = (q.get("sslmode", [""])[0] or "").strip()

    return {
        "ENGINE": engine,
        "NAME": (parsed.path or "/")[1:] or "",
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or ""),
        "CONN_MAX_AGE": 60,
        "OPTIONS": ({"sslmode": sslmode} if sslmode else {}),
    }

DATABASES = {"default": db_from_url(env("DATABASE_URL"))}

# ——— Passwords ———
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Autenticación Django (para authenticate() en /auth/login)
AUTHENTICATION_BACKENDS = [
    "usuarios.backends.EmailOrLocalBackend",   # tu backend: email o local-part
    "django.contrib.auth.backends.ModelBackend",
]


# ——— i18n ———
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# ——— Static/Media ———
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ——— DRF / JWT / Filters ———
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "usuarios.auth_cookie.CookieJWTAuthentication",  # cookies HttpOnly
        "rest_framework_simplejwt.authentication.JWTAuthentication",  # Bearer fallback
        "rest_framework.authentication.SessionAuthentication",        # admin
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "50/min", "user": "200/min"},
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

# —— JWT (SimpleJWT) —— 
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_DAYS", "7"))),
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# —— Cookies JWT —— 
JWT_LOGIN_RETURN_TOKENS = env_bool("JWT_LOGIN_RETURN_TOKENS", False)
JWT_AUTH_COOKIE         = env("JWT_AUTH_COOKIE", "access")
JWT_AUTH_REFRESH_COOKIE = env("JWT_AUTH_REFRESH_COOKIE", "refresh")
JWT_COOKIE_SAMESITE     = env("JWT_COOKIE_SAMESITE", "Lax")
JWT_COOKIE_SECURE       = env_bool("JWT_COOKIE_SECURE", False)
JWT_COOKIE_DOMAIN       = (env("JWT_COOKIE_DOMAIN") or None)
JWT_COOKIE_PATH         = env("JWT_COOKIE_PATH", "/")

# ——— Logging ———
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"format": "%(levelname)s %(asctime)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "INFO")},
}

# ——— OpenAPI ———
SPECTACULAR_SETTINGS = {
    "TITLE": "Claro API",
    "DESCRIPTION": "API de auditorías/asignaciones",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ——— CORS / CSRF ———
CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS") or [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS") or [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

# ——— Email ———
EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
    if env_bool("EMAIL_CONSOLE", False)
    else "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@example.com")

# ——— Seguridad extra (proxy/SSL) ———
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ——— Rutas/roles middleware (si lo usas) ———
ROLE_ROUTE_RULES = {
    "/api/admin/": {"administrador"},
    "/api/asignaciones/": {"administrador", "tecnico"},
    "/api/auditorias/": {"administrador", "tecnico"},
    "/api/core/": {"administrador", "tecnico"},
}

# ——— WhatsApp (desactivado; futuro) ———
WHATSAPP_ENABLED   = env_bool("WHATSAPP_ENABLED", False)
WHATSAPP_TOKEN     = env("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID  = env("WHATSAPP_PHONE_ID", "")
WHATSAPP_TEST_TO   = env("WHATSAPP_TEST_TO", "")

BOOTSTRAP_ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL")
BOOTSTRAP_ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
BOOTSTRAP_ADMIN_FIRST_NAME = os.getenv("BOOTSTRAP_ADMIN_FIRST_NAME", "Admin")
BOOTSTRAP_ADMIN_LAST_NAME = os.getenv("BOOTSTRAP_ADMIN_LAST_NAME", "Demo")
