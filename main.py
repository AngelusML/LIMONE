from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import select

from src.models.limone_model import Limone, LimoneCreate, LimoneUpdate
from src.shared.database.session_db import SessionDep

# IMPORTANTE: aqui NO se crean tablas. El esquema lo maneja Alembic, que corre
# "alembic upgrade head" al arrancar (ver docker-compose.yml). create_all()
# desaparece porque NO puede agregar columnas a una tabla que ya existe: sirve
# para empezar, pero a partir de ahi te bloquea.

app = FastAPI(
    title="Limone API",
    description="API CRUD de limonadas hecha con FastAPI y SQLModel.",
    version="0.1.0",
)


@app.get("/", include_in_schema=False)
def root():
    """Redirige de la raiz a la documentacion.

    FastAPI no crea nada en "/" por defecto, asi que sin este endpoint la
    raiz responde 404. Redirigir a /docs es comodo: al abrir
    http://127.0.0.1:8000 caes directo en la documentacion.

    include_in_schema=False evita que aparezca en la lista de endpoints:
    no es un endpoint de la API, solo es un atajo.
    """
    return RedirectResponse(url="/docs")


# ---------------------------------------------------------------------------
# Ayudantes
# ---------------------------------------------------------------------------


def get_lemonada_or_404(session, limone_id: int) -> Limone:
    """Busca una limonada por id. Si no existe, corta con un 404.

    "raise" lanza un error que FastAPI convierte automaticamente en una
    respuesta HTTP y detiene la ejecucion de la funcion. Por eso no
    necesitas un "return" despues: nunca se llega.
    """
    limone = session.exec(select(Limone).where(Limone.id == limone_id)).one_or_none()
    if limone is None:
        raise HTTPException(status_code=404, detail="Limonada no encontrada")
    return limone


def check_name_available(session, name: str, ignore_id: int | None = None) -> None:
    """Verifica que no exista ya una limonada con ese nombre.

    ignore_id sirve para el PUT y el PATCH: si estas Actualizando la
    limonada 3, su propio nombre no debe contar como duplicado.

    "func.lower" pasa el texto a minusculas en la base de datos para que la
    comparacion no dependa de como lo escribio el usuario.
    """
    query = select(Limone).where(func.lower(Limone.name) == name.strip().lower())
    if ignore_id is not None:
        query = query.where(Limone.id != ignore_id)

    if session.exec(query).first() is not None:
        raise HTTPException(
            status_code=409, detail=f"La limonada '{name}' ya existe"
        )


def check_price(price: float) -> None:
    """Verifica que el precio tenga sentido.

    FastAPI ya se encarga de avisarte si "price" no es un numero. Esto es
    una regla de negocio, y las reglas de negocio las escribes tu.
    """
    if price <= 0:
        raise HTTPException(
            status_code=422, detail="El precio debe ser mayor que 0"
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/lemonades", status_code=201, tags=["Lemonades"])
def create_lemonade(data: LimoneCreate, session: SessionDep):
    """Crea una limonada nueva (C del CRUD)."""
    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=422, detail="El nombre no puede estar vacio"
        )

    check_name_available(session, name)
    check_price(data.price)

    limone = Limone(
        name=name,
        price=data.price,
        category=data.category,
        flavor=data.flavor,
    )
    session.add(limone)
    session.commit()
    session.refresh(limone)
    return limone


@app.get("/lemonades", tags=["Lemonades"])
def get_lemonades(session: SessionDep):
    """Devuelve todas las limonadas (R del CRUD)."""
    return session.exec(select(Limone).order_by(Limone.id)).all()


@app.get("/lemonades/{limone_id}", tags=["Lemonades"])
def get_lemonade(limone_id: int, session: SessionDep):
    """Devuelve una limonada por su id (R del CRUD)."""
    return get_lemonada_or_404(session, limone_id)


@app.put("/lemonades/{limone_id}", tags=["Lemonades"])
def update_lemonade(limone_id: int, data: LimoneCreate, session: SessionDep):
    """Reemplaza TODA la limonada (U del CRUD).

    Por eso recibe LimoneCreate (todos los campos obligatorios): en un PUT
    tienes que mandar el objeto completo.
    """
    limone = get_lemonada_or_404(session, limone_id)

    name = data.name.strip()
    if not name:
        raise HTTPException(
            status_code=422, detail="El nombre no puede estar vacio"
        )

    check_name_available(session, name, ignore_id=limone_id)
    check_price(data.price)

    limone.name = name
    limone.price = data.price
    limone.category = data.category
    limone.flavor = data.flavor

    session.add(limone)
    session.commit()
    session.refresh(limone)
    return limone


@app.patch("/lemonades/{limone_id}", tags=["Lemonades"])
def patch_lemonade(limone_id: int, data: LimoneUpdate, session: SessionDep):
    """Modifica SOLO los campos que le mandes (U del CRUD).

    Recibe LimoneUpdate (todos los campos opcionales), porque aqui mandas
    solo lo que quieres cambiar.
    """
    limone = get_lemonada_or_404(session, limone_id)

    # exclude_unset=True es la clave de todo este endpoint: se queda solo
    # con los campos que el cliente MANDO de verdad. Si no mandaste "name",
    # "name" no aparece en el diccionario y no se toca.
    changes = data.model_dump(exclude_unset=True)

    if "name" in changes:
        name = str(changes["name"]).strip()
        if not name:
            raise HTTPException(
                status_code=422, detail="El nombre no puede estar vacio"
            )
        check_name_available(session, name, ignore_id=limone_id)
        changes["name"] = name

    if "price" in changes:
        check_price(float(changes["price"]))

    for field, value in changes.items():
        setattr(limone, field, value)

    session.add(limone)
    session.commit()
    session.refresh(limone)
    return limone


@app.delete("/lemonades/{limone_id}", tags=["Lemonades"])
def delete_lemonade(limone_id: int, session: SessionDep):
    """Borra una limonada (D del CRUD)."""
    limone = get_lemonada_or_404(session, limone_id)
    session.delete(limone)
    session.commit()
    return {"detail": "Limonada eliminada correctamente"}
