from sqlalchemy import create_engine, text
import psycopg2
import sys

# Mostrar información de entorno
print(f"Python version: {sys.version}")
print(f"Default encoding: {sys.getdefaultencoding()}")

# Configuración de conexión
host = 'localhost'
port = 5432
user = 'lender'
password = 'lender1$'
database = 'Lender'

# 1. Enfoque directo con psycopg2 - Especifica client_encoding
print("\n=== Intento 1: Conexión directa con psycopg2 ===")
try:
    print("Intentando conexión con psycopg2...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=database,
        options="-c client_encoding=utf8"
    )
    print("Conexión exitosa con psycopg2")
    cur = conn.cursor()
    cur.execute("SELECT * FROM credito LIMIT 5")
    rows = cur.fetchall()
    print(f"Datos encontrados: {len(rows)} filas")
    conn.close()
except Exception as e:
    print(f"Error con psycopg2: {str(e)}")

# 2. SQLAlchemy con parámetros de codificación
print("\n=== Intento 2: SQLAlchemy con parámetros de codificación ===")
try:
    print("Creando engine de SQLAlchemy con configuración de codificación...")
    # Usando el parámetro client_encoding en la URL de conexión
    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{database}?client_encoding=utf8'
    engine = create_engine(connection_string)
    
    with engine.connect() as connection:
        print("Conexión establecida")
        result = connection.execute(text('SELECT * FROM credito LIMIT 5'))
        print("Consulta ejecutada correctamente")
        rows = result.fetchall()
        print(f"Datos encontrados: {len(rows)} filas")
except Exception as e:
    print(f"Error con SQLAlchemy (client_encoding): {str(e)}")

# 3. SQLAlchemy con conexión básica ASCII
print("\n=== Intento 3: SQLAlchemy con conexión simple ===")
try:
    print("Creando engine de SQLAlchemy básico...")
    # URL más simple posible
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    
    with engine.connect() as connection:
        print("Conexión establecida")
        # Probando con una consulta simple primero
        result = connection.execute(text('SELECT 1 as test'))
        print("Consulta simple exitosa")
        
        # Ahora intentando la consulta a la tabla
        result = connection.execute(text('SELECT count(*) FROM credito'))
        count = result.scalar()
        print(f"Conteo de registros en credito: {count}")
except Exception as e:
    print(f"Error con SQLAlchemy básico: {str(e)}")

print("\nSi todos los intentos fallaron, verifica:")
print("1. La codificación de tu base de datos: Ejecuta 'SHOW server_encoding;' en PostgreSQL")
print("2. Que no haya caracteres especiales en nombres de tablas, usuarios o contraseñas")
print("3. Que el driver psycopg2 esté correctamente instalado: pip install psycopg2 o psycopg2-binary")
print("4. Que el usuario tenga permisos para acceder a la tabla credito")