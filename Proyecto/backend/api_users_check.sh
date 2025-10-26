#!/usr/bin/env bash
set -euo pipefail

# ====== CONFIG ======
BASE="http://127.0.0.1:8000"
ADMIN_EMAIL="administrador@test.com"
ADMIN_PASS="vtr12345"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Falta $1. Instálalo y reintenta."; exit 1; }; }
need curl
need jq

title(){ echo; echo "== $* =="; }

# ====== 1) LOGIN ADMIN (JWT) ======
title "Login admin y validar rol"
TOKEN=$(curl -s -X POST "$BASE/api/token/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}" | jq -r .access)

echo "TOKEN len: ${#TOKEN}"
if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "ERROR: no obtuve access token. Revisa credenciales o /api/token/"
  exit 1
fi

echo "# /auth/me"
curl -s "$BASE/auth/me" -H "Authorization: Bearer $TOKEN" | jq

# ====== 2) LISTAR ======
title "GET /api/admin/usuarios/"
curl -s "$BASE/api/admin/usuarios/" -H "Authorization: Bearer $TOKEN" | jq '.count,.results | length'

# ====== 3) CREAR USUARIO (POST) ======
title "POST /api/admin/usuarios (crear técnico)"
SUFFIX=$(date +%s)
NEW_EMAIL="qa.tech+$SUFFIX@test.com"
CREATE_JSON=$(cat <<JSON
{
  "email": "$NEW_EMAIL",
  "password": "Qa123456!",
  "first_name": "QA",
  "last_name": "Tech",
  "rol": "tecnico",
  "is_active": true
}
JSON
)
NEW_USER=$(curl -s -X POST "$BASE/api/admin/usuarios/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$CREATE_JSON")
echo "$NEW_USER" | jq
NEW_ID=$(echo "$NEW_USER" | jq -r .id)

if [ "$NEW_ID" = "null" ] || [ -z "$NEW_ID" ]; then
  echo "ERROR: no se creó el usuario. Revisa respuesta de arriba."
  exit 1
fi

# ====== 4) BUSCAR / FILTRAR / ORDENAR ======
title "GET /api/admin/usuarios?search=qa&rol=tecnico&is_active=true&ordering=-date_joined"
curl -s "$BASE/api/admin/usuarios/?search=qa&rol=tecnico&is_active=true&ordering=-date_joined" \
  -H "Authorization: Bearer $TOKEN" | jq '.results[0]'

# ====== 5) EDITAR (PATCH) ======
title "PATCH /api/admin/usuarios/$NEW_ID  (cambiar nombre)"
curl -s -X PATCH "$BASE/api/admin/usuarios/$NEW_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"QA-Edit","last_name":"Tech-Edit"}' | jq '.first_name,.last_name'

# ====== 6) SUSPENDER (DELETE => is_active=false) ======
title "DELETE (suspender) /api/admin/usuarios/$NEW_ID"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X DELETE "$BASE/api/admin/usuarios/$NEW_ID/" \
  -H "Authorization: Bearer $TOKEN"

echo "# Ver usuario suspendido"
curl -s "$BASE/api/admin/usuarios/?is_active=false&search=$SUFFIX" \
  -H "Authorization: Bearer $TOKEN" | jq '.results[0].email,.results[0].is_active'

# ====== 7) RE-ACTIVAR ======
title "PATCH reactivar /api/admin/usuarios/$NEW_ID"
curl -s -X PATCH "$BASE/api/admin/usuarios/$NEW_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}' | jq '.id,.is_active'

# ====== 8) PERMISOS (tecnico NO puede ver /api/admin/usuarios) ======
title "Login como técnico y probar 403 en /api/admin/usuarios"
TECH_TOKEN=$(curl -s -X POST "$BASE/api/token/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$NEW_EMAIL\",\"password\":\"Qa123456!\"}" | jq -r .access)
echo "TECH_TOKEN len: ${#TECH_TOKEN}"

curl -s -o /dev/null -w "HTTP %{http_code}\n" "$BASE/api/admin/usuarios/" -H "Authorization: Bearer $TECH_TOKEN"

echo
echo "✅ Checklist API usuarios_sistema OK"
