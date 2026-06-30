import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "tienda_db"

def get_db():
    """
    Establece la conexión con MongoDB y retorna la base de datos.
    """
    try:
        # Se establece un timeout corto (3 segundos) para verificar conexión rápidamente
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        # Forzar una llamada para comprobar la conexión activa
        client.admin.command('ping')
        return client[DB_NAME]
    except ConnectionFailure:
        print("\n[ERROR] No se pudo establecer conexión con el servidor de MongoDB.")
        print(f"Por favor, asegúrese de que el servicio de MongoDB esté iniciado en: {MONGO_URI}")
        sys.exit(1)
    except PyMongoError as e:
        print(f"\n[ERROR] Ocurrió un error inesperado de base de datos: {e}")
        sys.exit(1)
