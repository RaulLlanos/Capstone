# claro_project/settings.py
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# === Básico ===
SECRET_KEY = 'django-insecure-6k&s^egk4=lz7&mwlzt7=9o@9t@3mfz50a1fst+34)syl^*)ir'
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# === Apps ===
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'rest_framework',
    'django_filters',
    'corsheaders',
    'drf_spectacular',   # 📘 OpenAPI/Swagger

    # Apps del proyecto
    'usuarios',
    'asignaciones',
    'auditoria',
]

AUTH_USER_MODEL = 'usuarios.Usuario'

# === Middleware (CORS debe ir antes de CommonMiddleware) ===
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # CORS primero
    'corsheaders.middleware.CorsMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# === CORS/CSRF para permitir cookies desde el front ===
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True  # ← necesario para enviar cookies

# === URLS / WSGI ===
ROOT_URLCONF = 'claro_project.urls'
WSGI_APPLICATION = 'claro_project.wsgi.application'

# === Templates ===
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# === Base de datos: PostgreSQL ===
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "db_claro",
        "USER": "claro_user",
        "PASSWORD": "Claro_2025_pg",   # tu clave
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}

# === Password validators ===
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# === i18n ===
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# === Static & Media ===
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# === JWT (SimpleJWT): access corto, refresh largo ===
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# --- Cookies para JWT (para autenticación vía cookie HttpOnly) ---
JWT_AUTH_COOKIE = 'access'       # nombre de la cookie de access
JWT_AUTH_REFRESH_COOKIE = 'refresh'
JWT_COOKIE_SAMESITE = 'Lax'      # en prod, si front/back son dominios distintos: 'None'
JWT_COOKIE_SECURE = False        # en prod True (HTTPS)
JWT_COOKIE_PATH = '/'
JWT_COOKIE_DOMAIN = None         # en prod: tu dominio, ej. ".midominio.com"

# === DRF ===
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # 1) Primero: lee JWT desde cookie (usuarios/auth_cookie.py)
        'usuarios.auth_cookie.CookieJWTAuthentication',
        # 2) Soporte para Authorization: Bearer ...
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 3) Sesión (útil para /admin y browsable API)
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ),
    # Paginación
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,

    # OpenAPI/Swagger con drf-spectacular
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# === drf-spectacular (OpenAPI) ===
SPECTACULAR_SETTINGS = {
    'TITLE': 'ClaroVTR API',
    'DESCRIPTION': 'API para asignaciones y auditorías',
    'VERSION': '1.0.0',
}

# === Hash de contraseñas (bcrypt primero) ===
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # compatibilidad
]

# === Backends de autenticación (email o “local-part”) ===
AUTHENTICATION_BACKENDS = [
    'usuarios.backends.EmailOrLocalBackend',     # backend custom
    'django.contrib.auth.backends.ModelBackend', # fallback
]

# Límites de subida (coinciden con validación de fotos)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB por request
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB por archivo
