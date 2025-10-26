# claro_project/__init__.py
import os

if os.getenv("DB_ENGINE", "").endswith("mysql"):
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except Exception:
        pass
