# Guía 2: PostgreSQL, migraciones y Docker

En esta guía le pones a tu API lo que le faltaba para ser un proyecto real:
una base de datos de verdad, migraciones versionadas, y todo empaquetado en
Docker para que funcione en cualquier computador.

**Antes de empezar:** termina la guía 1 y confirma que tu CRUD funciona.

> **Todo lo de esta guía fue ejecutado y probado** en este computador: se
> construyó la imagen, se levantó PostgreSQL, se aplicó la migración y se
> probaron los 6 endpoints. Los errores de la sección 10 son **reales**, los
> encontré durante esas pruebas.

## El objetivo en una línea

```powershell
docker compose up -d --build
```

Ese **único comando** construye la imagen, arranca PostgreSQL, espera a que
esté sano, aplica las migraciones de Alembic y deja tu API en
`http://localhost:8000`. No hay un paso 2. Todo lo que sigue existe para que
entiendas **qué está pasando dentro de ese comando**.

---

## Qué vas a entender aquí

| Gu��a | Base de datos | ¿Cómo se crea la tabla? | ¿Dónde corre? |
|---|---|---|---|
| Guía 1 | SQLite (un archivo) | `create_all` al arrancar | Tu computador |
| **Guía 2 (esta)** | **PostgreSQL (un servidor)** | **Alembic, con migraciones** | **Dentro de Docker** |

---

## Por qué cambiar

**SQLite** es un archivo. Sirve perfecto para aprender y para prototipos, pero
PostgreSQL es lo que se usa en producción, y te da:

- Muchos usuarios leyendo y escribiendo a la vez (SQLite no).
- Tipos más ricos, mejores consultas, índices.
- Un servidor de verdad, al que se conectan otras máquinas.

**Alembic** porque `create_all` tiene un límite serio: **solo crea tablas que no
existen.** Si mañana agregas el campo `size` a tu tabla, `create_all` no hace
nada. No sabe "agregar una columna", solo "crear la tabla entera". Alembic sí
entiende los cambios y te escribe el `ALTER TABLE` correcto.

**Docker** porque "en mi computador funciona" no es una respuesta aceptable.
Con Docker, tu API y PostgreSQL viajan en un paquete que arranca igual en
cualquier lado.

---

## Paso 1 — Preparar `.env` para dos mundos

🎯 **Objetivo:** tener las variables listas para Docker.

💡 **Por qué:** tu app va a necesitar una dirección de base de datos, y esa
dirección **cambia según dónde corra la app**. Este es el punto que más confunde
a todo el mundo, así que léelo dos veces.

| ¿Dónde corre la app? | ¿Dónde está la base? | Host en la URL |
|---|---|---|
| En tu computador (uvicorn) | En tu computador | `localhost` |
| En Docker (compose) | En otro contenedor | `postgres` |

Dentro de Docker, `localhost` significa **el propio contenedor de tu app**, no tu
computador. Por eso dentro de Docker la base se llama `postgres` (el nombre del
servicio en el compose). Este es el error nº 1 de los que verás en la sección 10.

📝 **`.env`** — reemplaza todo el contenido:

```dotenv
# Base de datos para cuando corres la API en TU COMPUTADOR (SQLite, un archivo).
# Dentro de Docker no se usa: docker-compose.yml define su propia DATABASE_URL
# y load_dotenv() no sobreescribe variables que ya existen.
DATABASE_URL=sqlite:///./limone.db

# Datos de PostgreSQL. Los lee docker-compose.yml para crear la base de datos
# y para que la app se conecte.
DB_USER=limone_user
DB_PASSWORD=limone_password
DB_NAME=limone_db
```

**Nota de seguridad:** `DB_PASSWORD` está en texto plano. En un proyecto real se
genera al azar y se guarda en un gestor de secretos. Para un proyecto de
estudiante está bien, pero no subas este archivo a ningún repositorio público.

✅ **Verificar:** la API de la guía 1 sigue funcionando (SQLite no cambió).

---

## Paso 2 — Instalar Alembic

🎯 **Objetivo:** tener la herramienta de migraciones lista.

💡 **Por qué:** Alembic viene incluido en `fastapi[standard]`, así que probablemente
ya la tengas. Pero su comando es `alembic`, no `fastapi`, y conviene confirmar
que existe.

```powershell
uv run alembic --version
```

Debe mostrar algo como `alembic 1.20.x (already installed)`. Si dice que no se
reconoce, instálala:

```powershell
uv add "alembic>=1.20.0"
```

✅ **Verificar:** el comando anterior muestra un número de versión.

---

## Paso 3 — Crear el esqueleto de Alembic

🎯 **Objetivo:** tener la carpeta `alembic/` y su archivo de configuración.

💡 **Por qué:** `alembic init` genera una estructura estándar: los archivos que
controlan las migraciones y la carpeta donde viven. Es un andamiaje, no hay que
escribirlo a mano.

### 3.1 Genera la estructura

```powershell
uv run alembic init alembic
```

Eso crea:

```
alembic/
  env.py            <-- el archivo que hay que EDITAR (es el importante)
  script.py.mako    <-- la plantilla de cada migración
  versions/         <-- aquí van las migraciones
  README
alembic.ini         <-- configuración general
```

### 3.2 Revisa `alembic.ini`

Abre `alembic.ini` y busca estas dos líneas:

```ini
script_location = %(here)s/alembic
```

```ini
prepend_sys_path = .
```

**Si ya están así, no toques nada** — `alembic init` las crea correctas. La
primera le dice a Alembic dónde está la carpeta de migraciones. La segunda le
dice que agregue la carpeta del proyecto al path de Python, para que
`from src.models...` funcione.

La línea `sqlalchemy.url` que aparece ahí **no la vamos a usar** (dice
`driver://user:pass@localhost/dbname`, un valor falso). La sobrescribimos con
la variable de entorno en el siguiente paso.

### 3.3 Edita `alembic/env.py`

Este es el archivo clave, y tiene **tres** cambios importantes.

📝 **`alembic/env.py`** — reemplaza todo el contenido por esto:

```python
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
```

**Sobre el `# noqa: F401`:** es un comentario que le dice a los linters "ya sé
que `Limone` no se usa, es un import intencional". Es la forma estándar de
marcar un import que existe solo por un efecto secundario.

✅ **Verificar:** el archivo no tiene errores de sintaxis:

```powershell
uv run python -c "import ast; ast.parse(open('alembic/env.py').read()); print('sintaxis OK')"
```

---

## Paso 4 — Quitar el `create_all` de `main.py`

🎯 **Objetivo:** que solo Alembic administre la estructura de la base de datos.

💡 **Por qué:** si dejas los dos mecanismos activos, se pelean. `create_all`
crearía la tabla al arrancar y Alembic cree que nunca la migración, y viceversa.
Con el tiempo esto genera migraciones fantasma y confusiones.

Con migraciones hay **una sola fuente de verdad**: Alembic.

📝 **`main.py`** — haz estos tres cambios:

**1. Borra el import de `contextlib` y el bloque `lifespan`:**

```python
# BORRAR ESTAS DOS LINEAS
from contextlib import asynccontextmanager

# ...

# BORRAR TODO ESTE BLOQUE
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield
```

**2. Quita el `lifespan` del constructor de la app:**

```python
# ANTES
app = FastAPI(
    title="Limone API",
    description="API CRUD de limonadas hecha con FastAPI y SQLModel.",
    version="0.1.0",
    lifespan=lifespan,
)

# DESPUES
app = FastAPI(
    title="Limone API",
    description="API CRUD de limonadas hecha con FastAPI y SQLModel.",
    version="0.1.0",
)
```

**3. Quita `engine` de los imports** (ya no se usa en `main.py`):

```python
# ANTES
from src.shared.database.session_db import SessionDep, engine

# DESPUES
from src.shared.database.session_db import SessionDep
```

**Los endpoints NO cambian.** Ni una línea. Ese es el punto de haber separado las
capas: cambiar la base de datos no tocó la lógica.

✅ **Verificar:** el archivo sigue starting sin errores y `/docs` sigue
mostrando los 6 endpoints.

---

## Paso 5 — El `docker-compose.yml`

🎯 **Objetivo:** describir los dos servicios y cómo se conectan.

💡 **Por qué:** `docker-compose.yml` es el mapa de tu sistema. Al leerlo de arriba
abajo, entiendes qué corre, quién depende de quién y qué datos se guardan. Este
archivo es documentación que además funciona.

📝 **`docker-compose.yml`** — crea este archivo:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      # ${...} se rellena con tu .env (compose lo lee solo, sin exportar nada)
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    ports:
      - "5433:5432"        # 5433:5432 en tu PC. Ver la nota de abajo
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      # "healthy" = hay alguien contestando. El servicio de abajo espera a eso.
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
    volumes:
      - .:/app              # tu codigo sobre /app: recarga automatica
    # Este command reemplaza al CMD del Dockerfile:
    # 1) aplica las migraciones pendientes (si no hay, no hace nada)
    # 2) arranca uvicorn con recarga
    command: sh -c "alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
```

### Cómo leerlo

| Línea | Qué significa |
|---|---|
| `services:` | Empieza la lista de contenedores |
| `postgres:` | Nombre del servicio. **Este nombre es la dirección** que la app usa para encontrarla |
| `image: postgres:16-alpine` | Imagen oficial de PostgreSQL 16, versión `alpine` (más ligera) |
| `POSTGRES_USER: ${DB_USER}` | Toma el valor `DB_USER` de tu `.env` |
| `"5433:5432"` | **tu computador**:contenedor. Ver la nota de abajo |
| `volumes:` | Los datos viven fuera del contenedor y sobreviven |
| `DATABASE_URL: postgresql://...@postgres:5432/...` | **Aquí está el corazón**: el host es `postgres`, no `localhost` |
| `volumes: .:/app` | Monta tu código en el contenedor para la recarga automática |
| `command:` | Reemplaza al `CMD` del Dockerfile: migración y luego uvicorn |
| `depends_on: condition: service_healthy` | No arranques hasta que la base esté sana |

#### ⚠️ Por qué el puerto es 5433 y no 5432

En tu computador **ya hay un PostgreSQL local corriendo** (el servicio de
Windows `postgresql-x64-18`) y ocupa el 5432. Si pones `"5432:5432"`, Docker
no puede asignarlo y te sale:

```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

**La solución es no pelear por el puerto:** usamos `5433` en tu PC y listo.

**La parte izquierda es el de tu computador, la derecha el de dentro del
contenedor.** Cambia solo la izquierda. La derecha debe quedar siempre `5432`,
porque es el puerto interno de PostgreSQL.

Esto **no afecta a la aplicación**: dentro de la red de Docker, tu app se
conecta al servicio `postgres` en el puerto `5432`, que es el de dentro. El
`5433` solo lo usas tú, desde DBeaver o `psql`, para mirar la base.

#### ⚠️ El volumen `postgres_data`: no lo saltes

Si un volumen viejo quedó con una contraseña distinta (por ejemplo de un
intento anterior), PostgreSQL **no te deja entrar** y verás:

```
FATAL: password authentication failed for user "limone_user"
```

La solución es borrar **solo el volumen de este proyecto** y empezar de cero:

```powershell
docker compose down
docker volume rm limone_postgres_data
docker compose up -d postgres
```

⚠️ Fíjate en el nombre: `limone_postgres_data`. El volumen de otro proyecto
(¡por ejemplo el de Luigi!) no lo toques.

#### Sobre `alpine` vs la imagen normal

Luigi usa `postgres:16` y tú usas `postgres:16-alpine`. La versión `alpine`
es bastante más pequeña (más rápida de descargar). Ambas funcionan. Si tienes
problemas raros con `alpine`, cambia a `postgres:16` y ya.

✅ **Verificar:**

```powershell
docker compose config
```

Este comando **valida** el archivo sin arrancar nada. Si escribe el YAML
completo por pantalla, tu compose está bien escrito. Es el equivalente a "pásame
el borrador antes de imprimirlo".

---

## Paso 6 — El `Dockerfile`

🎯 **Objetivo:** construir una imagen con tu app dentro.

💡 **Por qué multi-stage:** para instalar librerías hacen falta herramientas de
compilación que ocupa mucho espacio. Un `python:slim` no las tiene, y **no las
debería tener en producción**: son peso muerto y riesgo de seguridad. El truco es
instalar en una imagen grande y copiar **solo el resultado** a una imagen
pequeña.

📝 **`Dockerfile`** — crea este archivo:

```dockerfile
# =============================================================================
# Etapa 1: BUILDER
# Imagen grande que solo sirve para instalar dependencias. No se distribuye.
# =============================================================================
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

# UV_PROJECT_ENVIRONMENT: donde uv crea el venv. Va en /opt/venv (fuera de
# /app) y no en /app/.venv por una razon concreta: en desarrollo montamos tu
# codigo en /app, y si el venv estuviera ahi tu .venv de Windows lo taparia y
# nada arrancaria. Ademas, los scripts de uvicorn/alembic guardan la ruta del
# venv en su shebang, asi que tiene que estar en su sitio desde el principio.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /build

# Copiar SOLO la configuracion de dependencias primero. Si no cambias
# pyproject.toml ni uv.lock, esta capa se cachea y el paso siguiente tarda
# un segundo en vez de volver a instalar todo.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Ahora si copiamos el codigo y dejamos el venv listo.
COPY . /build
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# =============================================================================
# Etapa 2: FINAL
# Imagen pequena: el venv con las dependencias y el codigo. Nada mas.
# =============================================================================
FROM python:3.14-slim

# PYTHONUNBUFFERED: saca los prints y logs al instante.
# PYTHONDONTWRITEBYTECODE: no genera .pyc, para que --reload no vea archivos
# escribiendose dentro de /app y entre en bucle de reinicios.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# El proceso corre como usuario normal, NO como root. Si alguien logra entrar
# al contenedor, no tiene permisos de administrador.
RUN addgroup --system appgroup \
    && adduser --system --group appuser

# El venv viene de la etapa anterior, ya instalado en /opt/venv.
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# El codigo va a /app. En desarrollo este contenido lo tapa el volumen de
# docker-compose.yml (ese es justo el objetivo: ver tus cambios al instante).
COPY --chown=appuser:appgroup . /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Las piezas que hay que entender

**`--host 0.0.0.0` es obligatorio.** Por defecto uvicorn solo escucha en
`127.0.0.1`, que es "dentro del contenedor". Con `0.0.0.0` escucha en todas las
interfaces y Docker puede ayudarle. Si te sale `connection refused` desde el
navegador, casi seguro es esto.

**El venv va en `/opt/venv` y no en `/app/.venv`.** Esta es la diferencia más
importante con el Dockerfile de la guía. En el paso 5 montaste tu código sobre
`/app` para la recarga automática; si el venv estuviera dentro de `/app`, tu
`.venv` de Windows lo taparía y nada arrancaría. Por eso:

- `UV_PROJECT_ENVIRONMENT=/opt/venv` le dice a `uv` dónde crearlo **desde el principio**.
  No basta con copiarlo después a otro sitio: los scripts de `uvicorn` y `alembic`
  guardan la ruta del venv en su cabecera (`shebang`), así que tiene que vivir en
  su sitio desde el primer momento.
- `PATH="/opt/venv/bin:$PATH"` evita escribir la ruta completa cada vez.

**`--reload` en el `CMD`.** Es el que hace la magia de "guardas y se actualiza
solo". Junto con `PYTHONDONTWRITEBYTECODE=1` (que evita generar `.pyc`) impide
que la app escriba archivos dentro de `/app` y entre en un bucle de reinicios.

**`--frozen` significa "respeta el `uv.lock` a rajatabla".** No recalcula
versiones durante la construcción. Sin él, cada `docker build` podría instalar
versiones distintas y tu imagen no sería reproducible.

**`--no-install-project`** va porque quitamos `[build-system]` del
`pyproject.toml`, así que `uv` no intenta instalar el proyecto como paquete. Es
justo lo que hace Luigi en su `dockerfile`, por el mismo motivo.

**El truco del `COPY pyproject.toml uv.lock ./` antes del código** es la
optimización más importante de un Dockerfile. Docker guarda cada instrucción
como una capa, y si una capa no cambia, la reutiliza. Si copiaras todo el código
primero, cada cambio en `main.py` obligaría a reinstalar 50 librerías.

**`CMD` en el `Dockerfile` y `command` en el compose:** el `command` del
compose **reemplaza** al `CMD` del Dockerfile. Aquí los dos existen a propósito:

| | Qué hace |
|---|---|
| `CMD` del Dockerfile | Arranca uvicorn con `--reload`. Vale si usas `docker run` suelto |
| `command` del compose | `alembic upgrade head && uvicorn ...` — la migración antes de servir |

Al final, en compose manda el `command`. El `CMD` se queda para que `docker run`
funcione sin compose.

✅ **Verificar:** construimos la imagen en el paso 8.

---

## Paso 7 — `.dockerignore`

🎯 **Objetivo:** que no se meta basura en la imagen.

💡 **Por qué importa:** `COPY . /app` copia **absolutamente todo** de la carpeta,
incluidas cosas que no quieres dentro. Sin `.dockerignore`:

| Se copiaría | Por qué es malo |
|---|---|
| `.venv/` | Tu entorno virtual de **Windows**. Pesaría gigabytes y dentro del contenedor **no funciona** (estaba compilado para otro sistema) |
| `.env` | ¡Tu contraseña! Dentro de la imagen, visible para cualquiera |
| `__pycache__/` | Basura generada |
| `*.db` | Tu base de datos local |

Este archivo es el que hace que tu imagen no pese 3 GB.

📝 **`.dockerignore`** — crea este archivo:

```gitignore
# Nada de esto hace falta dentro de la imagen.
# Menos archivos = build mas rapido y imagen mas limpia.

# Control de versiones y documentacion
.git
.gitignore
guias
README.md

# Entornos virtuales (dentro de Docker no usas tu .venv de Windows)
.venv
__pycache__
*.py[cod]

# Seguridad: los secretos NUNCA se hornean en la imagen.
# El docker-compose.yml pasa las variables al contenedor en tiempo de arranque.
.env
.env.local
.env.example

# Bases de datos locales
*.db

# El propio despliegue
Dockerfile
.dockerignore
docker-compose.yml

# IDEs
.vscode
.idea
```

Ojo con `.env` aquí: **no entra en la imagen**, pero sí entra en tiempo de
ejecución a través del volumen `.:/app` del compose. No pasa nada porque
`load_dotenv()` no sobreescribe variables que ya existen, y el compose ya puso
la `DATABASE_URL` de PostgreSQL antes de arrancar Python. Es una defensa en dos
capas.

**Compáralo con el `.gitignore` del paso 7 de la guía 1:** casi igual. La
diferencia clave es que `.gitignore` protege de subir a internet, y
`.dockerignore` protege de meter cosas en la imagen. Se complementan, no se
sustituyen.

✅ **Verificar:** después de construir, el peso de la imagen debe ser razonable
(unos 200-300 MB, no varios GB).

---

## Paso 8 — La primera migración y **un solo comando**

🎯 **Objetivo:** que PostgreSQL tenga la tabla `limone`, creada por Alembic, y
arrancar todo de una vez.

💡 **Por qué este orden importa:** Alembic **compara** tu modelo de Python con la
base de datos y te dice qué falta. Para que la comparación signifique algo, **la
base tiene que estar vacía**. Si ya tiene la tabla (porque un `create_all` la
creó), Alembic concluirá que no hay nada que hacer y generará un archivo vacío.

### 8.1 Levanta solo PostgreSQL

```powershell
docker compose up -d postgres
```

La primera vez que lo corro se verá algo así:

```
Volume limone_postgres_data Creating   ... Done
Container limone-postgres-1 Starting   ... Done
Container limone-postgres-1 Healthy
```

**`Healthy` es la señal de que el `healthcheck` funciona.** Si no llega a
`Healthy`, revisa `docker compose logs postgres`.

### 8.2 Genera la migración **dentro del contenedor**

```powershell
docker compose run --rm app alembic revision --autogenerate -m "crear tabla limone"
```

Salida esperada (la línea clave es la primera):

```
INFO  [alembic.autogenerate.compare.tables] Detected added table 'limone'
Generating /app/alembic/versions/ae4e3b224752_crear_tabla_limone.py ...  done
```

**`Detected added table 'limone'`** es la línea que quieres ver. Si no aparece,
Alembic no vio tu modelo: vuelve al paso 3.3 y revisa el **Cambio 1**.

**Por qué dentro del contenedor y no desde PowerShell:** así Alembic usa la
misma `DATABASE_URL`, el mismo driver y la misma base a la que se va a aplicar
la migración. Si la generas desde tu PC contra SQLite, te sale SQL de SQLite y
PostgreSQL lo rechaza. `docker compose run` arranca un contenedor temporal con
el mismo servicio (y levanta `postgres` como dependencia), ejecuta el comando y
lo borra: no deja nada sucio. El `--rm` es justamente "borra el contenedor al
terminar".

El archivo nuevo aparece en tu carpeta `alembic/versions/`, porque el volumen
`.:/app` lo escribió de verdad en tu disco.

### 8.3 Revisa el archivo generado

**Ábrelo y Léelo.** Esto es importante: `autogenerate` no es perfecto, y tú eres
la última línea de defensa antes de tocar la base de datos.

Debe verse así:

```python
from sqlalchemy import String

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "limone",
        sa.Column("name", String(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column(
            "category",
            sa.Enum("CLASSIC", "TROPICAL", "EXOTIC", "BERRY", name="lemonadecategories"),
            nullable=False,
        ),
        sa.Column("flavor", String(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
```

Tres cosas que notarás:

1. **`String()` y no `AutoString()`** — gracias al Cambio 3. Si ves
   `sqlmodel.sql.sqltypes.AutoString()`, el Cambio 3 no se aplicó. Y si te
   falta el `from sqlalchemy import String` del principio, tampoco.
2. **`CLASSIC`, `TROPICAL`... en mayúsculas** — el enum se guarda con el *nombre*
   del miembro, no con su valor. La API seguirá devolviendo `"Classic"`.
3. **`id` va al final y es `nullable=False`** — normal en un autogenerate.

### 8.4 El comando único

```powershell
docker compose up -d --build
```

La primera vez tarda un poco (descarga Python, uv y las librerías); verás las
etapas numeradas (`#1`, `#2`...) y `CACHED` en las que ya estaban. A partir de
ahí, **ese es el comando que corres siempre**.

**Salida esperada, en este orden exacto:**

```
Container limone-postgres-1  Healthy
Container limone-app-1       Starting
Container limone-app-1       Started
```

Si ves `Healthy` **antes** de `Starting`, tu `depends_on` funciona.

Mira los logs de la app para ver la migración aplicarse sola:

```powershell
docker compose logs app
```

```
INFO  [alembic.runtime.migration] Running upgrade  -> ae4e3b224752, crear tabla limone
INFO:     Will watch for changes in these directories: ['/app']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Eso es todo.** `alembic upgrade head` corrió antes de uvicorn, creó la tabla y
ya puede servir peticiones. Si no hay migraciones pendientes, ese mismo comando
no hace nada y sigue con el arranque: por eso puede correr en cada inicio sin
romper nada.

⚠️ **Si la migración falla, la app NO arranca.** Es a propósito: es mejor un
error claro en los logs que una base de datos a medias.

### 8.5 Comprueba que corren

```powershell
docker compose ps
```

Debes ver los dos servicios con estado `Up`, y `healthy` en el de PostgreSQL.

```powershell
docker compose exec postgres psql -U limone_user -d limone_db -c "SELECT * FROM limone;"
```

Si responde, la conexión es real.

### 8.6 Prueba la API

Abre **http://localhost:8000/docs** y repite las 12 pruebas de la guía 1.

**Si todo funciona, tu API ahora corre sobre PostgreSQL real dentro de Docker.**

✅ **Verificar:** las 12 pruebas dan el resultado esperado, y los datos
sobreviven a `docker compose restart app`.

---

## Paso 9 — Comandos del día a día

### Con Docker

| Quiero... | Comando |
|---|---|
| **Arrancar todo** | `docker compose up -d --build` |
| Ver qué corre | `docker compose ps` |
| Ver los logs | `docker compose logs -f app` |
| Detener (conserva los datos) | `docker compose stop` |
| Reiniciar | `docker compose restart app` |
| Reconstruir sin arrancar | `docker compose build` |
| **Borrar todo, datos incluidos** | `docker compose down -v` |
| Ver los logs de PostgreSQL | `docker compose logs -f postgres` |

⚠️ **`docker compose down -v` borra el volumen**, y con él **todos tus datos**.
Es tu herramienta de "empezar de cero".

### Con Alembic

Usa `docker compose exec app ...` para que corra **dentro del contenedor**, con
la misma base que usa tu API:

| Comando | Qué hace |
|---|---|
| `docker compose exec app alembic current` | Qué migración está aplicada |
| `docker compose exec app alembic history` | Historial de migraciones |
| `docker compose exec app alembic upgrade head` | Aplica lo pendiente |
| `docker compose exec app alembic downgrade -1` | Retrocede una migración |
| `docker compose exec app alembic revision --autogenerate -m "..."` | Genera una migración nueva |

💡 **La próxima vez que agregues un campo** (por ejemplo `size`): lo agregas al
modelo, corres `revision --autogenerate` y después `upgrade head`. Nada más.

```powershell
docker compose exec app alembic revision --autogenerate -m "agregar campo size"
docker compose exec app alembic upgrade head
```

El archivo nuevo aparece en `alembic/versions/`. Eso es versionar la base de
datos.

### En local, sin Docker

Sigue funcionando con SQLite, para iterar rápido:

```powershell
uv run uvicorn main:app --reload
```

---

## Paso 10 — Errores reales que vas a encontrar

Los encontré probando esta guía en tu computador. Están en el orden en que los
vas a topar.

### 1. `Bind for 0.0.0.0:5432 failed: port is already allocated`

**Qué significa:** ya hay algo usando el 5432 de tu computador.

**Por qué pasa en tu caso:** tienes el servicio de Windows **`postgresql-x64-18`**
(PostgreSQL 18) corriendo y ocupándolo. Te lo comprobé:

```powershell
Get-Service | Where-Object { $_.Name -match 'postgre' }
```

**Solución — no pelees por el puerto.** Por eso el compose usa `"5433:5432"`:
el 5433 es para ti, el 5432 sigue siendo el de dentro del contenedor. Si en
algún momento cambias algo, recuerda que solo se toca la **izquierda**.

Si prefieres liberar el 5432 de todas formas (no hace falta para esta guía):

```powershell
Stop-Service postgresql-x64-18
```

### 2. `NameError: name 'sqlmodel' is not defined`

**Cuándo:** al hacer `alembic upgrade head` sobre una migración autogenerada.

**Por qué:** este es el error más traicionero de SQLModel + Alembic. El archivo
de migración generado contiene esto:

```python
sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
```

Fíjate: usa `sqlmodel` pero **el archivo solo importa `sqlalchemy`**. Cuando
Python llega a esa línea, truena. Es un problema conocido entre las dos
herramientas.

**Solución:** el `render_item` del **Cambio 3** del paso 3.3. Con esa función, el
archivo se genera con `String()` y con su `from sqlalchemy import String`
correcto. **Si ya te pasó**, borra la migración y genera otra:

```powershell
Remove-Item alembic\versions\*.py
docker compose up -d postgres
docker compose run --rm app alembic revision --autogenerate -m "crear tabla limone"
```

### 3. `DuplicateObject: type "lemonadecategories" already exists`

**Cuándo:** al hacer `alembic upgrade head` después de que una migración anterior
fallara a medio camino.

**Por qué:** PostgreSQL creó el tipo enum, pero la migración se rompió antes de
terminar. Quedó el tipo suelto, y la nueva migración intenta crearlo otra vez.

**Solución:** lo más rápido es empezar de cero (borra también las migraciones
rotas):

```powershell
Remove-Item alembic\versions\*.py
docker compose down -v
docker compose up -d postgres
docker compose run --rm app alembic revision --autogenerate -m "crear tabla limone"
docker compose up -d --build
```

Si necesitas conservar los datos, borra solo el tipo huérfano:

```powershell
docker compose exec postgres psql -U limone_user -d limone_db -c "DROP TYPE IF EXISTS lemonadecategories CASCADE;"
```

### 4. `connection refused` al abrir `localhost:8000`

**Causas, en orden de probabilidad:**

1. **Falta el `--host 0.0.0.0`** en el `CMD`. Si lo quitaste, el contenedor
   está escuchando solo para sí mismo.
2. **El contenedor murió.** Míralo: `docker compose ps`. Si dice `Exited`, mira
   `docker compose logs app` para ver el error real.
3. **Mapeo de puerto equivocado.** Debe ser `"8000:8000"`.

### 5. `FATAL: password authentication failed for user "limone_user"`

**Cuándo:** al generar o aplicar la migración, o al arrancar la app.

**Por qué:** existe un volumen `limone_postgres_data` **viejo**, de un intento
anterior, inicializado con otras credenciales. Los contenedores se borran y se
crean cuantas veces quieras, pero **el volumen no**: conserva la base de datos
de cuando se creó, incluido su usuario. Te lo comprobé en tu máquina: el mío
decía `role "limone_user" does not exist`.

Compruébalo:

```powershell
docker volume ls          # ¿existe limone_postgres_data?
docker volume inspect limone_postgres_data --format '{{.CreatedAt}}'
```

**Solución:** borrar **solo el volumen de este proyecto**:

```powershell
docker compose down
docker volume rm limone_postgres_data
docker compose up -d postgres
```

⚠️ Fíjate en el nombre completo: `limone_postgres_data`. **No toques el volumen
de otro proyecto** (por ejemplo el de Luigi, `fastapi_luigui_postgres_data`).

### 6. `no such table: limone`

**Por qué:** quitaste el `create_all` (paso 4) pero nunca aplicaste la migración,
o estás en local y no corriste `alembic upgrade head`.

**Solución en Docker:**

```powershell
docker compose exec app alembic upgrade head
```

**Solución en local (SQLite):**

```powershell
uv run alembic upgrade head
```

💡 **Este error es buena noticia:** significa que Alembic está haciendo su
trabajo. La tabla ya no la crea tu código al arrancar, la crea la migración.
Como debe ser.

### 7. `connection refused` hacia PostgreSQL desde la app

**Por qué:** la URL apunta a `localhost` en vez de a `postgres`.

**Regla fácil de recordar:**

| Si la app corre... | El host es... |
|---|---|
| Dentro de Docker | `postgres` (el nombre del servicio) |
| En tu computador | `localhost` |

Dentro de un contenedor, `localhost` es **el propio contenedor de la app**, que
no tiene base de datos propia.

### 8. `error: failed to solve: ... no such file or directory: uv.lock`

**Por qué:** el `Dockerfile` hace `COPY pyproject.toml uv.lock ./`, pero no
existe `uv.lock`.

**Solución:** créalo con `uv lock` dentro de la carpeta del proyecto. Y **súbelo
a Git**: es el archivo que garantiza que todos instalan lo mismo.

### 9. La API responde, pero los datos desaparecen al reiniciar

**Por qué:** PostgreSQL corre **sin volumen**, o el volumen se borró con
`docker compose down -v`.

**Revisa** que el compose tenga las dos cosas:

```yaml
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

y al final del archivo:

```yaml
volumes:
  postgres_data:
```

### 10. La app se reinicia en bucle, sin parar

**Cuándo:** los logs muestran `WatchFiles detected changes` una y otra vez.

**Por qué:** `--reload` ve archivos cambiando dentro de `/app` que no deberían
cambiar (por ejemplo un `.db` si la app estuviera usando SQLite dentro del
contenedor, o los `.pyc` si quitaras `PYTHONDONTWRITEBYTECODE`).

**Solución:** comprueba que `DATABASE_URL` del compose apunta a PostgreSQL y que
`PYTHONDONTWRITEBYTECODE=1` sigue en el `Dockerfile`.

---

## ✅ Checklist: proyecto terminado

### Base de datos y migraciones

- [ ] `psycopg2-binary` en `pyproject.toml` (para PostgreSQL)
- [ ] `alembic/env.py` con el import del modelo
- [ ] `alembic/env.py` con `DATABASE_URL` en mayúsculas
- [ ] `alembic/env.py` con la función `render_item`
- [ ] Existe `alembic/versions/` con tu migración
- [ ] La migración usa `String()` y trae su `from sqlalchemy import String`
- [ ] `alembic current` muestra `(head)`
- [ ] Quitaste `create_all` y el `lifespan` de `main.py`

### Docker

- [ ] `Dockerfile` con dos etapas (`builder` y final)
- [ ] El venv se crea en `/opt/venv` (`UV_PROJECT_ENVIRONMENT`) y el `PATH` apunta ahí
- [ ] El `CMD` incluye `--host 0.0.0.0` y `--reload`
- [ ] Los dos `uv sync` llevan `--frozen`
- [ ] El código va en `USER appuser`, no root
- [ ] `.dockerignore` excluye `.venv`, `.env`, `*.db` y `guias`
- [ ] `docker-compose.yml` con los servicios `postgres` y `app`
- [ ] `depends_on` con `condition: service_healthy`
- [ ] El `DATABASE_URL` del compose apunta a `@postgres:5432`
- [ ] El `command` del compose hace `alembic upgrade head` **antes** de uvicorn
- [ ] El volumen `.:/app` está para la recarga automática
- [ ] Existe el volumen `postgres_data` (declarado y usado)
- [ ] El puerto publicado es `"5433:5432"` (tu PC ya usa el 5432)

### Funcionamiento

- [ ] **`docker compose up -d --build` arranca todo, solo, sin pasos extra**
- [ ] `docker compose ps` muestra los dos servicios `Up`
- [ ] Los logs muestran `Healthy` **antes** de `Starting`
- [ ] Los logs muestran `Running upgrade -> ..., crear tabla limone`
- [ ] `http://localhost:8000/docs` responde
- [ ] Los 6 endpoints funcionan contra PostgreSQL
- [ ] `SELECT * FROM limone;` devuelve los datos
- [ ] `docker compose stop` / `up -d` conserva los datos
- [ ] Guardar `main.py` recarga la app sola (`WatchFiles detected changes`)
- [ ] En local, `uv run uvicorn main:app --reload` sigue funcionando con SQLite

### Documentación

- [ ] `README.md` actualizado con el comando de arranque único
- [ ] `.env` sin subir a Git
- [ ] `.env.example` con las variables sin valores secretos
- [ ] Segundo commit hecho

---

## Lo que lograste

Repasemos el viaje, porque no es poco:

| Etapa | Qué aprendiste |
|---|---|
| Antes | Una API a medio hacer, con un entorno virtual roto |
| Guía 1 | Un CRUD completo y probado: 6 endpoints, validaciones, documentación |
| Guía 2 | PostgreSQL real, migraciones versionadas, Docker, y despliegue reproducible |

**Y lo mejor: entiendes *por qué* está cada cosa.** Eso vale más que el código.

### Si quieres seguir creciendo

| Siguiente paso | En qué consiste |
|---|---|
| **Tests automáticos** | `pytest` con `TestClient` para verificar los endpoints sin navegador. Fue lo que usé para validar esta guía. |
| **Autenticación** | Login con usuarios y contraseñas, y proteger los endpoints |
| **Paginación** | `GET /lemonades?limit=10&offset=20` para no devolver 100 000 registros |
| **Filtros** | `GET /lemonades?category=Classic` para buscar |
| **CI/CD** | Que los tests corran solos en cada cambio |
| **Despliegue** | Subirlo a un servidor real con un dominio y HTTPS |

Sugerencia: los **tests automáticos** son el siguiente paso natural, porque ya
tienes la lógica lista y solo falta verificarla automáticamente. Y de paso
descubres por quéreeze se escriben tests: yo verifiqué estas guías con 20 pruebas
sin abrir el navegador ni una vez.
