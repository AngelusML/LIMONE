import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import Session, create_engine

# Lee el archivo .env y pone sus variables disponibles en el programa.
load_dotenv()

# Si no encuentra DATABASE_URL, usa SQLite local (un simple archivo).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./limone.db")

# El engine se crea UNA vez y se reusa. "echo=True" imprime el SQL que se
# ejecuta: es util mientras aprendes (veras cada INSERT, SELECT, etc).
# Cuando tu proyecto este estable, ponlo en False para que no ensucie la consola.
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    """Le entrega a FastAPI una sesion con la base de datos.

    El "with" abre la sesion al entrar y la CIERRA al salir, aunque la
    funcion falle. Por eso usamos esto y no un session = Session(engine)
    suelto: nada se queda abierto.
    """
    with Session(engine) as session:
        yield session


# La "firma" que usaran todos los endpoints.
# Traduccion: "el parametro 'session' es de tipo Session, y su valor
# me lo da get_session()".
SessionDep = Annotated[Session, Depends(get_session)]
