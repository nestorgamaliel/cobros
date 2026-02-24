import sys
from os.path import abspath, dirname, join
from dotenv import load_dotenv
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1. Cargar Entorno
BASE_DIR = abspath(dirname(dirname(__file__)))
load_dotenv(join(BASE_DIR, ".env"))
sys.path.insert(0, BASE_DIR)

# 2. IMPORTACIÓN DE CONFIGURACIÓN Y MODELOS
from config import settings 
from app.models.models import Base

alembic_config = context.config
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

target_metadata = Base.metadata

# --- LÓGICA DE FILTRADO Y PROTECCIÓN ---
def get_ignored_tables():
    ignore_file = join(BASE_DIR, "alembic_ignore.txt")
    try:
        with open(ignore_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

TABLAS_IGNORADAS = get_ignored_tables()

def include_object(object, name, type_, reflected, compare_to):
    # A. Ignorar tablas que están en el archivo TXT
    if type_ == "table" and name in TABLAS_IGNORADAS:
        return False
    
    # B. PROTECCIÓN CRÍTICA: 
    # Si el objeto existe en la DB (reflected=True) pero NO está definido en models.py (compare_to=None),
    # devolvemos False para que Alembic NO genere un DROP (borrado).
    # Esto protege tus Triggers, Índices (como el del DUI) y FKs de municipio/departamento.
    if reflected and compare_to is None:
        return False

    return True
# ---------------------------------------

def run_migrations_offline() -> None:
    url = settings.SQLALCHEMY_DATABASE_URI
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = alembic_config.get_section(alembic_config.config_ini_section)
    if configuration is None:
        configuration = {}
    
    configuration["sqlalchemy.url"] = settings.SQLALCHEMY_DATABASE_URI

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_object=include_object 
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()