# core/views_health.py
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response

class Healthz(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"ok": True})

class Readyz(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1;")
            db_ok = True
        except Exception as e:
            db_ok = False
        return Response({"ok": db_ok, "db": db_ok})
