import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import String, engine_from_config, pool
from sqlmodel import SQLModel
from sqlmodel.sql.sqltypes import AutoString

# --- CAMBIO 1 (CRITICO) -------------------------------------------------
# Alembic solo conoce las tablas que le digas importar. Sin esta linea,
# el comando "autogenerate" no ve la tabla Limone y genera una migracion
# VACIA (sin ningun create_table).
from src.models.limone_model import Limone  # noqa: F401

from dotenv import load_dotenv

load_dotenv()

config = context.config

# --- CAMBIO 2 ------------------------------------------------------------
# La URL real SIEMPRE viene de la variable de entorno DATABASE_URL, nunca
# de una linea fija en el codigo. Esto es justamente lo que Luigi hace
# mal: su env.py pide "DATABASE_URL" pero su .env define "Database_url".
# En Windows funciona (las mayusculas no importan), en Docker se rompe.
#
# Si no esta definida, cae en SQLite: es lo que te deja correr en local
# sin Docker, igual que la API.
database_url = os.getenv("DATABASE_URL", "sqlite:///./limone.db")
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


# --- CAMBIO 3 ------------------------------------------------------------
# SQLModel tiene un tipo de dato propio llamado AutoString, que Alembic no
# sabe escribir bien: genera "sqlmodel.sql.sqltypes.AutoString()" en la
# migracion pero SIN importar sqlmodel. La migracion revienta con:
#     NameError: name 'sqlmodel' is not defined
# Esta funcion le dice a Alembic que use el String normal de SQLAlchemy.
def render_item(type_, obj, autogen_context):
    if type_ == "type" and isinstance(obj, AutoString):
        autogen_context.imports.add("from sqlalchemy import String")
        return "String()"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
