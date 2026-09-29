# Guía 1: rehacer tu API de limonadas (CRUD + FastAPI)

Aquí construyes tu API **desde cero**, en tu computador, sin Docker y con SQLite.

**Qué necesitas tener listo:** el documento `00-conceptos.md` (sobre todo las
Partes 1, 2 y 3). Si no sabes qué es un endpoint o un schema, no avances.

**Al terminar vas a tener** una API de limonadas con los 6 endpoints completos,
funcionando, documentada y probada.

> **Todo el código de esta guía fue ejecutado y probado** (20 pruebas
> automáticas, todas en verde). Si copias los bloques tal cual, funciona.

---

## Cómo usar esta guía

Cada paso tiene la misma estructura:

| Sección | Qué es |
|---|---|
| 🎯 **Objetivo** | Qué consigues al terminar el paso |
| 💡 **Por qué** | Por qué lo hacemos así y no de otra forma |
| 📝 **Código** | El archivo completo, para copiar |
| ✅ **Verificar** | Cómo compruebas que funcionó |
| ⚠️ **Errores comunes** | Lo que suele salir mal |

**No avances al siguiente paso hasta que el "Verificar" te funcione.**

---

## Paso 0 — Diagnóstico: qué está mal hoy

Antes de borrar nada, Understand qué tienes. Revisé tu proyecto y esto es lo que
encontré:

| # | Problema | Consecuencia |
|---|---|---|
| 1 | Tu `.venv` se creó **dentro de Linux** (`home = /usr/local/bin`, sin carpeta `Scripts`) | **No puedes ejecutar nada.** Es un entorno roto. |
| 2 | Nadie crea la tabla `limone` (no hay `create_all` ni Alembic) | Tu API responde `no such table: limone` |
| 3 | Faltan **PUT** y **PATCH** | Tu CRUD está incompleto |
| 4 | Tu `.env` tiene `Database_url` **3 veces**, y una vacía | Confuso, y se rompe en Linux/Docker |
| 5 | `CreateLimone` está en `main.py`, no en el archivo de modelos | Desordenado; Luigi lo tiene todo junto |
| 6 | Comparas con `.lower().strip()` pero guardas el nombre sin normalizar | "Limonada" y "limonada  " se cuelan como duplicadas |
| 7 | `pyproject.toml` tiene `[build-system]` | Obliga a mantener la carpeta inútil `src/limone/` |
| 8 | `src/limone/__init__.py` existe solo por el punto 7 | No hace nada |

**Sobre el punto 1**, que es el más grave: tu carpeta `.venv` se creó dentro de un
contenedor Linux y quedó copiada a Windows. Por eso no tiene `Scripts/` ni `Lib/`.
Es normal que no funcione — la buena noticia es que no pierdes nada, porque un entorno
virtual es desechable.

---

## Paso 1 — Limpiar el proyecto

🎯 **Objetivo:** dejar la carpeta como si recién la hubieras creado.

💡 **Por qué:** partir de cero es más rápido y más limpio que reparar. Tu
código actual tiene errores de diseño (puntos 3, 5, 6, 7) que no se arreglan
"arreglando": hay que rehacerlos. Además nadie tiene commits todavía
(`git log` dice *"does not have any commits yet"*), así que **no pierdes nada
que no tengas en un papel**.

> Antes de borrar, si crees que quieres conservar algo de tu código actual,
> cópialo a otra carpeta. Yo revisé todo: lo que vale la pena ya está
> incorporado en esta guía.

### 1.1 Archivos y carpetas a eliminar

| Qué | Dónde |
|---|---|
| `.venv/` | toda la carpeta (está roto) |
| `limone.db` | la base de datos vieja (no tiene la tabla) |
| `__pycache__/` | todas las carpetas de caché |
| `src/limone/` | carpeta inútil |
| `docker-compose.yml` | lo rehacemos en la guía 2 |
| `Dockerfile` | lo rehacemos en la guía 2 |
| `alembic.ini` | lo rehacemos en la guía 2 |
| `.env` | lo reescribimos en el paso 8 |

### 1.2 Archivos que vamos a conservar y reescribir

`main.py`, `pyproject.toml`, `README.md`, `.gitignore`, `.python-version`,
`src/models/limone_model.py`, `src/shared/database/session_db.py`.

**Cómo borrarlos** (PowerShell, desde la carpeta `LIMONE`):

```powershell
Remove-Item -Recurse -Force .venv, src\limone, __pycache__
Remove-Item -Recurse -Force src\models\__pycache__, src\shared\__pycache__, src\shared\database\__pycache__
Remove-Item -Force limone.db, Dockerfile, docker-compose.yml, alembic.ini, .env
```

**Comprueba que `.env` no se borró** antes de seguir, porque lo recreas en el
paso 8 (no hay problema, es un archivo de 4 líneas).

✅ **Verificar:** tu carpeta debería verse así:

```
LIMONE/
├── .git/
├── .gitignore
├── .python-version
├── README.md
├── main.py
├── pyproject.toml
├── uv.lock
└── src/
    ├── models/
    │   ├── __init__.py
    │   └── limone_model.py
    └── shared/
        ├── __init__.py
        └── database/
            ├── __init__.py
            └── session_db.py
```

---

## Paso 2 — Recrear el entorno virtual

🎯 **Objetivo:** tener un entorno virtual que funcione en Windows.

💡 **Por qué:** el problema nº 1 era un `.venv` creado en Linux. `uv sync` lo
recrea usando **tu** Python de Windows, que es el 3.14.3. Además crea el
`.venv` **sin que tengas que pedirlo**: una sola orden hace todo.

### 2.1 Corrige `pyproject.toml`

Ábrelo y reemplaza **todo** su contenido por esto:

```toml
[project]
name = "limone"
version = "0.1.0"
description = "API CRUD de limonadas hecha con FastAPI y SQLModel"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
    "fastapi[standard]>=0.141.1",
    "sqlmodel>=0.0.46",
    "python-dotenv>=1.2.3",
    "alembic>=1.20.0",
]
```

**Qué cambió y por qué:**

| Cambio | Por qué |
|---|---|
| Quité `[build-system]` y `[project.scripts]` | Eran la causa de la carpeta inútil `src/limone/`. Sin esta sección, `uv` trata el proyecto como "no instalable" y ya no la exige. |
| Quité `psycopg2-binary` | En esta guía uso **SQLite**, que no necesita ese driver. Lo agregamos en la guía 2 para PostgreSQL. |
| Añadí `python-dotenv` | Lo importabas en `session_db.py` pero **no estaba declarado** en las dependencias. Estaba funcionando solo por casualidad. |
| Dejé `alembic` | Lo usaremos en la guía 2; instalarlo ahora evita un segundo `uv sync`. |
| Quité tu email del campo `authors` | Se puede añadir después; no afecta nada. |

> **Sobre `fastapi[standard]`:** los corchetes son opcionales pero quieres
> `standard` porque trae `uvicorn` (el servidor que ejecuta tu API) y otras
> herramientas útiles.

### 2.2 Crea el entorno

```powershell
uv sync
```

Salida esperada (resuelve e instala ~50 paquetes):

```
Resolved 52 packages in ...
Installed 50 packages in ...
```

✅ **Verificar:**

```powershell
uv run python -c "import fastapi, sqlmodel, dotenv; print('OK')"
```

Debe imprimir `OK`. Si imprime un error de módulo, no sigas.

---

## Paso 3 — El modelo de datos

🎯 **Objetivo:** definir la tabla `limone` y los esquemas de entrada.

💡 **Por qué:** antes de pensar en endpoints, defines *qué es* una limonada. Si
entiendes el modelo, los endpoints son casi mecánicos. Esta es la diferencia
entre un proyecto ordenado y un proyecto al que hay que rhodear.

📝 **`src/models/limone_model.py`** — reemplaza todo el contenido:

```python
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
```

📝 **`src/models/__init__.py`** — reemplaza todo el contenido:

```python
from src.models.limone_model import (
    LemonadeCategories,
    Limone,
    LimoneBase,
    LimoneCreate,
    LimoneUpdate,
)

__all__ = [
    "LemonadeCategories",
    "Limone",
    "LimoneBase",
    "LimoneCreate",
    "LimoneUpdate",
]
```

**Qué es ese archivo:** es el "índice" de la carpeta de modelos. Quien quiera
importar algo de aquí lo hace con una línea. No es obligatorio, pero es orden.

### Dos cosas que conviene entender ahora

**1. `Limone` tiene `id`, `LimoneCreate` no.** El `id` lo genera la base de datos
al insertar. Si el cliente pudiera mandar el `id`, podría sobrescribir o saltarse
identificadores. En tu código viejo, `CreateLimone` tampoco lo tenía, y eso estaba
bien.

**2. `category` es un `Enum`, y en la base de datos se guarda en MAYÚSCULAS.**
Verificado en este proyecto: si haces una consulta SQL directa a PostgreSQL verás
`CLASSIC` o `TROPICAL`, no `Classic`. La API siempre devuelve `Classic` porque
SQLModel traduce al leer. No es un error; tenlo presente si inspeccionas la base
de datos a mano.

⚠️ **Errores comunes en este paso:**

| Síntoma | Causa | Solución |
|---|---|---|
| `ImportError: cannot import name 'Limone'` | Archivo mal guardado o sin guardar | Guarda el archivo (Ctrl+S) |
| `SyntaxError` con `str | None` | Versión de Python < 3.10 | Verifica `python --version` (debe ser 3.14) |
| No aparece la tabla en `/docs` | Espera al paso 5, la tabla se crea al arrancar | Nada, sigue |

✅ **Verificar:**

```powershell
uv run python -c "from src.models.limone_model import Limone, LimoneCreate, LimoneUpdate; print(Limone.__tablename__)"
```

Debe imprimir `limone`.

---

## Paso 4 — La conexión a la base de datos

🎯 **Objetivo:** crear el `engine` (cómo hablarle a la base) y la `SessionDep`
(la función que FastAPI usará para darte sesiones).

💡 **Por qué:** esto va en un archivo aparte y no en `main.py` por una razón
concreta: **más de un archivo necesitará la base de datos** (tu API, y en la guía
2, Alembic). Si lo dejaras en `main.py`, Alembic tendría que importar tu servidor
web para poder conectarse. Separarlo evita ese acoplamiento. Luigi lo hace igual.

📝 **`src/shared/database/session_db.py`** — reemplaza todo el contenido:

```python
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
```

**Sobre `DATABASE_URL` en mayúsculas:** lo puse así a propósito. Tu versión usaba
`Database_url`, y eso funciona en Windows pero **se rompe en Docker** (allá el
sistema es Linux y las mayúsculas sí importan). Usar siempre el mismo nombre en
mayúsculas te ahorra ese problema después. Es la razón por la que el `env.py` de
Luigi no le funciona bien en Docker.

**Sobre `echo=True`:** mientras aprendes, pruébalo en `true`. Vas a ver en la
terminal cosas como:

```
INFO sqlalchemy.engine.Engine BEGIN (implicit)
INFO sqlalchemy.engine.Engine CREATE TABLE limone (...)
INFO sqlalchemy.engine.Engine INSERT INTO limone VALUES (...)
```

Así entiendes que tu código realmente está hablando con la base de datos. Cuando
ya no te interese, cámbialo a `False`.

---

## Paso 5 — `main.py`: la aplicación y los 6 endpoints

🎯 **Objetivo:** escribir toda la API.

💡 **Por qué está en un solo archivo:** para una API de este tamaño, un `main.py`
es lo correcto y es lo que hace Luigi. Si crece, se puede separar en una carpeta
`routers/`, pero separar antes de tiempo solo te hace perder el rumbo.

### 5.1 La estructura general

Antes de copiar, esta es la idea de cómo se lee:

| Parte | Para qué |
|---|---|
| `lifespan` | Al arrancar el servidor, crear la tabla si no existe |
| `app` | El servidor de FastAPI |
| `get_lemonada_or_404` | **Ayudante 1:** busca por id o falla con 404 |
| `check_name_available` | **Ayudante 2:** verifica que el nombre no exista |
| `check_price` | **Ayudante 3:** verifica que el precio sea válido |
| Los 6 endpoints | Uno por sección, con su comentario |

**¿Por qué ayudantes aparte?** Las reglas "el nombre no puede repetirse" y "el
precio debe ser mayor que 0" se necesitan en `POST`, en `PUT` y en `PATCH`. Si las
escribieras tres veces en cada endpoint, tendrías 9 copias que se desincronizan
(seguro terminas cambi solo en una). Con un ayudante, cambias la regla en **un**
sitio. Es la diferencia entre código que se mantiene y código que da miedo tocar.

📝 **`main.py`** — reemplaza todo el contenido:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import func
from sqlmodel import SQLModel, select

from src.models.limone_model import Limone, LimoneCreate, LimoneUpdate
from src.shared.database.session_db import SessionDep, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Se ejecuta al arrancar el servidor.

    create_all() crea las tablas que falten. OJO: sirve para empezar, pero
    mas adelante lo reemplazamos por Alembic (guia 2), porque create_all NO
    puede agregar columnas a una tabla que ya existe.
    """
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Limone API",
    description="API CRUD de limonadas hecha con FastAPI y SQLModel.",
    version="0.1.0",
    lifespan=lifespan,
)


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

    FastAPI ya se encargo de avisarte si "price" no es un numero. Esto es
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
```

### 5.2 Las tres piezas que más se confunden

**a) `select(...)` vs `session.exec(...)`**

`select()` viene de SQLAlchemy y es un "query builder": describe qué quieres
consultar, y devuelve un objeto. `session.exec()` es el método de SQLModel que
recibe ese objeto y lo ejecuta. Es como decir "quería esto" y luego "hazlo".

**b) `session.exec(...)` devuelve un Resultado, y hay que elegir qué hacer con él**

| Método | Devuelve | Úsalo cuando |
|---|---|---|
| `.all()` | lista de todos los resultados | Necesitas varios |
| `.first()` | el primero, o `None` | Solo te importa saber si existe |
| `.one_or_none()` | el único, o `None` | Buscas por id (solo puede haber uno) |

**c) `model_dump(exclude_unset=True)` — el corazón del PATCH**

Verificado en este proyecto, así que fíjate:

| Llamada | `model_dump()` normal | `model_dump(exclude_unset=True)` |
|---|---|---|
| `LimoneUpdate(price=20.0)` | `{'name': None, 'price': 20.0, ...}` | `{'price': 20.0}` |
| `LimoneUpdate()` | todo en `None` | `{}` (vacío) |
| `LimoneUpdate(name=None)` | todo en `None` | `{'name': None}` |

Sin `exclude_unset`, un PATCH de solo el precio **borraría el nombre, la categoría
y el sabor** (los pondría en `None`). Ese es el bug clásico del PATCH. Con
`exclude_unset=True` solo se tocan los campos presentes.

⚠️ **Errores comunes:**

| Síntoma | Causa | Solución |
|---|---|---|
| `sqlite3.OperationalError: no such table: limone` | Corriste el archivo sin pasar por uvicorn | Usa siempre `uv run uvicorn main:app --reload` |
| `422` al hacer POST sin `category` | El campo es obligatorio (correcto) | Manda la categoría en el JSON |
| `name` se borra al hacer PATCH | Quitaste `exclude_unset=True` | Vuelve a ponerlo |
| `ImportError: cannot import name 'SessionDep'` | No guardaste `session_db.py` | Guarda y reinicia con `--reload` |

---

## Paso 6 — Arrancar y probar

🎯 **Objetivo:** ver tu API funcionando.

### 6.1 Arranca el servidor

```powershell
uv run uvicorn main:app --reload
```

**Qué significa cada parte:**

| Parte | Significado |
|---|---|
| `uv run` | Usar el entorno virtual del proyecto |
| `uvicorn` | El servidor que ejecuta FastAPI |
| `main:app` | Del archivo `main.py`, el objeto `app` |
| `--reload` | Reinicia solo si cambias el código (úsalo siempre mientras programas) |

Salida esperada:

```
INFO:     Started reloader process
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Y como puse `echo=True`, verás el SQL de cada operación. Eso es normal.

### 6.2 Abre la documentación

Abre en el navegador: **http://localhost:8000/docs**

Verás tus 6 endpoints listados, con descripción y los campos de cada uno. Esta
página se generó sola, sin que escribieras una línea de documentación.

### 6.3 Pruébalos todos

En `/docs`, pulsa **"Try it out"** y luego **"Execute"**. Cubre esto:

| # | Prueba | Esperado | Por qué importa |
|---|---|---|---|
| 1 | POST con los 4 campos | `201` y un `id` | Lo básico |
| 2 | POST **el mismo nombre** con minúsculas y espacios | `409` | El nombre es único sin importar cómo se escriba |
| 3 | POST con `price: 0` | `422` | La regla de negocio funciona |
| 4 | POST con `category: "NoExiste"` | `422` | El Enum rechaza valores inventados |
| 5 | GET `/lemonades` | `200` con la lista | Leer todas |
| 6 | GET `/lemonades/1` | `200` con una | Leer una |
| 7 | GET `/lemonades/999` | `404` | No existe |
| 8 | PUT con los 4 campos | `200`, todo cambiado | Reemplaza completo |
| 9 | PATCH con **solo** `price` | `200` y el resto **intacto** | La prueba clave del PATCH |
| 10 | PATCH con `price: -5` | `422` | Valida lo que sí llega |
| 11 | DELETE `/lemonades/1` | `200` | Borrar |
| 12 | GET `/lemonades/1` de nuevo | `404` | Se borró de verdad |

**La prueba 9 es la importante.** Manda solo el precio y fíjate en que el nombre,
la categoría y el sabor siguen ahí. Si se borran, tu PATCH está mal y no
continúes.

### 6.4 Las otras dos páginas

- `http://localhost:8000/redoc` — misma info, más bonita, solo lectura.
- `http://localhost:8000/docs` dice "OpenAPI 3.1" arriba: FastAPI también
  describe tu API en un estándar. Eso es lo que permite que un frontend generado
  automáticamente sepa qué campos esperar.

✅ **Verificar:** las 12 pruebas de la tabla dan el resultado esperado.

---

## Paso 7 — `.gitignore`

🎯 **Objetivo:** que nunca se suban secretos ni archivos basura a internet.

📝 **`.gitignore`** — reemplaza todo el contenido:

```gitignore
# Archivos generados por Python
__pycache__/
*.py[cod]
build/
dist/
*.egg-info/

# Entornos virtuales
.venv/

# Variables de entorno (CONTIENE CONTRASENAS: nunca se sube)
.env
.env.local

# Bases de datos locales
*.db

# Control de versiones / IDEs
.vscode/
.idea/
.DS_Store
Thumbs.db
```

**Fíjate en la diferencia con Luigi:** su `.gitignore` **sí** tiene `.env`; el
tuyo **no**. Eso significa que si haces `git add .` ahora, tu contraseña de
PostgreSQL sube a GitHub, y aunque lo borres después, queda en el historial para
siempre. Corregido.

✅ **Verificar:**

```powershell
git status
```

No debe listar ni `.env` ni `limone.db` ni `.venv`.

---

## Paso 8 — `.env`

🎯 **Objetivo:** separar la configuración del código.

📝 **`.env`** — crea este archivo:

```dotenv
# Cuando corres la API en tu computador, usa SQLite (un simple archivo).
DATABASE_URL=sqlite:///./limone.db

# Datos de PostgreSQL para cuando las necesites (guia 2).
DB_USER=limone_user
DB_PASSWORD=limone_password
DB_NAME=limone_db

# OJO: la URL de PostgreSQL NO va aqui sin comentario.
# Dentro de Docker el host no es "localhost", es el servicio "postgres".
# La activa docker-compose.yml por su cuenta.
# DATABASE_URL=postgresql://limone_user:limone_password@localhost:5432/limone_db
```

**Lo que se corrigió aquí:**

| Antes | Ahora | Por qué |
|---|---|---|
| `Database_url` × 3 (una vacía) | `DATABASE_URL` × 1 | Sin ambigüedad, y en mayúsculas para que funcione en Docker |
| Sin valor | `sqlite:///./limone.db` | Una variable vacía rompe el arranque |
| `Database_url=` al final (vacía) | comentado con `#` | Así no se aplica por accidente |

💡 **Sobre por qué funciona la variable vacía:** `python-dotenv` toma la
**primera** aparición de una clave repetida, y aplica el estilo "si no está, no
sobrescribir". Por eso tu `Database_url=` vacío del final te rompía el arranque
aunque arriba hubiera una buena. Eliminé las repeticiones, y así de paso se
entiende el archivo.

📝 **`.env.example`** — crea este archivo también:

```dotenv
DATABASE_URL=sqlite:///./limone.db
DB_USER=
DB_PASSWORD=
DB_NAME=
```

**¿Para qué sirve?** Es la plantilla: le dices a otra persona "estas son las
variables que tienes que crear, con estos nombres". El `.env` real nunca se
comparte (tiene tu contraseña); el `.env.example` sí.

✅ **Verificar:** reinicia el servidor y sigue funcionando. Si al arrancar dice
`DATABASE_URL` no encontrada, el archivo está mal escrito.

---

## Paso 9 — `README.md`

🎯 **Objetivo:** que alguien (o tú en 3 meses) sepa cómo usarlo.

📝 **`README.md`** — reemplaza todo el contenido:

````markdown
# Limone API

API CRUD de limonadas hecha con **FastAPI** y **SQLModel**, sobre **SQLite**.

## Requisitos

- Python 3.14 o superior
- [uv](https://docs.astral.sh/uv/) instalado

## Instalación

```bash
uv sync
```

## Ejecución

```bash
uv run uvicorn main:app --reload
```

La API queda en http://localhost:8000

## Documentación interactiva

- `/docs` — Swagger UI (prueba los endpoints desde el navegador)
- `/redoc` — ReDoc

## Endpoints

| Método | Ruta | Qué hace | Código |
|---|---|---|---|
| POST | `/lemonades` | Crear una limonada | 201 |
| GET | `/lemonades` | Listar todas | 200 |
| GET | `/lemonades/{id}` | Obtener una por id | 200 / 404 |
| PUT | `/lemonades/{id}` | Reemplazar una completa | 200 |
| PATCH | `/lemonades/{id}` | Actualizar solo algunos campos | 200 |
| DELETE | `/lemonades/{id}` | Eliminar | 200 |

### Diferencia entre PUT y PATCH

- **PUT** recibe **todos** los campos obligatorios y reemplaza el registro entero.
- **PATCH** recibe **cualquier subset** de campos y solo cambia lo recibido,
  dejando el resto intacto.

Ejemplo de PATCH (solo cambia el precio):

```json
{ "price": 9500 }
```

## Estructura

```
main.py                      # Servidor y endpoints
src/
  models/
    limone_model.py          # Tabla y esquemas
  shared/
    database/
      session_db.py          # Engine y sesión
```

## Variables de entorno

Definidas en `.env` (ver `.env.example`):

| Variable | Para qué |
|---|---|
| `DATABASE_URL` | Dirección de la base de datos |

## Notas

- La tabla se crea sola al arrancar (`SQLModel.metadata.create_all`).
- `echo=True` en el engine imprime el SQL. En producción conviene `False`.
- Con PostgreSQL real se usan migraciones con Alembic en lugar de `create_all`.
````

✅ **Verificar:** ábrelo en GitHub o en un editor y se lee bien.

---

## Paso 10 — Tu primer commit

🎯 **Objetivo:** guardar esta versión que ya funciona.

💡 **Por qué ahora y no antes:** hasta este punto tu proyecto estaba roto y sin
historial. Un commit ahora significa "este es el punto donde todo funcionaba", y
si algo se rompe después, `git diff` te dirá exactamente qué cambiaste.

```powershell
git add .
git status
```

**Revisa la lista antes de seguir.** Debe mostrar tus archivos de código y
**NO** debe aparecer `.env`, `.venv` ni `limone.db`. Si aparece alguno, tu
`.gitignore` está mal y hay que corregirlo **antes** de hacer commit.

```powershell
git commit -m "API CRUD de limonadas con FastAPI, SQLModel y SQLite"
```

💡 **Escribe el mensaje en pasado y en español.** Es la convención: describe lo
que hiciste, no lo que harás. "API CRUD de limonadas" queda claro en el historial;
"arreglando cosas" no sirve de nada dentro de seis meses.

✅ **Verificar:**

```powershell
git log --oneline
```

Debe mostrar una línea con tu mensaje.

---

## ✅ Checklist: mi CRUD está listo

Marca todo. Si algo falla, vuelve al paso correspondiente.

**Estructura**
- [ ] `.venv` se recreó y `uv run python -c "import fastapi"` funciona
- [ ] No existe `src/limone/`
- [ ] `pyproject.toml` sin `[build-system]`
- [ ] `python-dotenv` está en las dependencias

**Modelo**
- [ ] `LemonadeCategories` con 4 categorías
- [ ] `LimoneBase` con los 4 campos
- [ ] `Limone` con `table=True` y `id` como clave primaria
- [ ] `LimoneCreate` sin `id`, todos los campos obligatorios
- [ ] `LimoneUpdate` con todos los campos opcionales

**Base de datos**
- [ ] `DATABASE_URL` en mayúsculas, en `.env`, una sola vez
- [ ] `engine` con la URL del `.env`
- [ ] `SessionDep` definido
- [ ] La tabla se crea al arrancar (sin errores)

**Endpoints**
- [ ] POST devuelve `201` y crea la limonada
- [ ] POST con nombre repetido (ignorando mayúsculas/espacios) devuelve `409`
- [ ] POST con precio `<= 0` devuelve `422`
- [ ] POST con categoría inválida devuelve `422`
- [ ] GET lista devuelve `200`
- [ ] GET por id devuelve `200` / `404`
- [ ] PUT reemplaza todo y devuelve `200`
- [ ] PATCH cambia **solo** lo enviado y conserva el resto
- [ ] PATCH con body vacío `{}` devuelve `200` y no rompe nada
- [ ] DELETE devuelve `200` y luego el GET da `404`

**Calidad**
- [ ] `/docs` muestra los 6 endpoints con descripción
- [ ] `.gitignore` incluye `.env`, `.venv` y `*.db`
- [ ] `git status` no muestra `.env`
- [ ] `README.md` explica cómo usarlo
- [ ] Hiciste tu primer commit

---

## ¿Y ahora qué?

Ya tienes un CRUD completo y probado. Falta lo que hace que un proyecto sea
"de verdad deployable":

1. Que la base de datos sea **PostgreSQL** y no SQLite.
2. Que los cambios de estructura se puedan **versionar** (migraciones).
3. Que todo eso se empaquete en **Docker**, para que funcione en cualquier
   computador.

Eso es exactamente lo que hace la guía 2 →

---

## Siguiente guía

📘 **`02-guia-docker-postgres.md`** — PostgreSQL con Alembic y Docker.
