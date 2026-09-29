from enum import Enum

from sqlmodel import Field, SQLModel


class LemonadeCategories(str, Enum):
    """Categorias permitidas para una limonada.

    Al ser un Enum, solo se aceptan estos 4 valores. Si alguien escribe
    "clasica" o "clasico", FastAPI lo rechaza con 422 automaticamente.
    """

    CLASSIC = "Classic"
    TROPICAL = "Tropical"
    EXOTIC = "Exotic"
    BERRY = "Berry"


class LimoneBase(SQLModel):
    """Los campos que comparte TODAS las versiones de Limone.

    Existe para no repetir estos 4 campos tres veces. Las clases de abajo
    heredan de aqui (se llama "herencia").
    """

    name: str
    price: float
    category: LemonadeCategories
    flavor: str


class Limone(LimoneBase, table=True):
    """El modelo que se guarda en la BASE DE DATOS.

    Ojo al "table=True": es lo que le dice a SQLModel "esto es una tabla".
    Solo esta clase tiene id, porque el id lo pone la base de datos.
    """

    __tablename__ = "limone"
    id: int | None = Field(default=None, primary_key=True)


class LimoneCreate(LimoneBase):
    """Lo que espera la API en un POST o un PUT.

    Hereda los 4 campos, todos OBLIGATORIOS (no tienen valor por defecto).
    Por eso un POST sin "name" falla con 422.
    """


class LimoneUpdate(SQLModel):
    """Lo que espera la API en un PATCH.

    Todos los campos son OPCIONALES (por eso el "| None = None"), porque en
    un PATCH solo mandas lo que quieres cambiar.
    """

    name: str | None = None
    price: float | None = None
    category: LemonadeCategories | None = None
    flavor: str | None = None
