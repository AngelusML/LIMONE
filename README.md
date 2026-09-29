# Limone API

API CRUD para una tienda de limonadas, hecha con **FastAPI** + **SQLModel** y
**PostgreSQL**, empaquetada con **Docker** y con migraciones versionadas
(**Alembic**).

**Arrancar todo con un solo comando:**

```powershell
docker compose up -d --build
```

Ese comando construye la imagen, arranca PostgreSQL, espera a que esté sano,
aplica las migraciones pendientes y deja la API en
**http://localhost:8000**. No hay paso 2.

---

## Índice

1. [Qué es esto](#1-qué-es-esto)
2. [Requisitos](#2-requisitos)
3. [Instalación: el primer día](#3-instalación-el-primer-día)
4. [Arrancar y parar](#4-arrancar-y-parar)
5. [Comprobar que funciona](#5-comprobar-que-funciona)
6. [Endpoints](#6-endpoints)
7. [Comandos del día a día](#7-comandos-del-día-a-día)
8. [Cambiar el código](#8-cambiar-el-código)
9. [Migraciones (Alembic)](#9-migraciones-alembic)
10. [Modo local, sin Docker](#10-modo-local-sin-docker)
11. [Puertos, variables de entorno y DBeaver](#11-puertos-variables-de-entorno-y-dbeaver)
12. [Estructura del proyecto](#12-estructura-del-proyecto)
13. [Problemas frecuentes](#13-problemas-frecuentes)
14. [Documentación y siguientes pasos](#14-documentación-y-siguientes-pasos)

---

## 1. Qué es esto

Una API de estilo CRUD: crea, lee, actualiza y borra limonadas.

| | |
|---|---|
| **Framework** | FastAPI |
| **ORM / modelos** | SQLModel (Pydantic + SQLAlchemy) |
| **Base de datos** | PostgreSQL 16 dentro de Docker; SQLite en local |
| **Migraciones** | Alembic |
| **Empaquetado** | Docker + Docker Compose |
| **Gestor de paquetes** | [uv](https://docs.astral.sh/uv/) |
| **Documentación** | Swagger UI automática en `/docs` |

**Lo que no es:** no hay usuarios, ni autenticación, ni carrito de compras. Es
la base sobre la que se construye todo lo demás.

### El esquema de datos

```
limone
-----------
id          integer   PRIMARY KEY (lo pone la base)
name        varchar   NOT NULL
price       float     NOT NULL
category    enum      NOT NULL   CLASSIC | TROPICAL | EXOTIC | BERRY
flavor      varchar   NOT NULL
```

> **Dato importante sobre `category`.** Es un Enum: solo acepta esos 4 valores.
> En la base de datos se guarda el **nombre en mayúsculas** (`CLASSIC`); la API
> devuelve el **valor** (`"Classic"`). Por eso verás mayúsculas en DBeaver y
> mayúscula inicial en el JSON. Los dos están bien.

---

## 2. Requisitos

| Programa | Para qué | ¿Obligatorio? |
|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Levantar PostgreSQL y la API | **Sí**, salvo que uses el modo local |
| [uv](https://docs.astral.sh/uv/) | Instalar Python y las librerías | Solo para modo local |
| [Git](https://git-scm.com/) | Descargar el proyecto | Sí |
| [DBeaver](https://dbeaver.io/) | Mirar la base de datos | Opcional |

Versiones con las que está probado todo esto:

```powershell
docker --version            # Docker 29.8.0
docker compose version      # Docker Compose v5.5.1
uv --version                # uv 0.12.19
uv python find              # Python 3.14.3
```

Si no tienes `uv`:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **No necesitas instalar PostgreSQL.** Viene dentro de Docker. De hecho, si
> en tu equipo ya hay un PostgreSQL local, **no lo toques**: el de este
> proyecto usa otro puerto (ver la sección 11).

---

## 3. Instalación: el primer día

```powershell
git clone <url-del-repositorio>
cd LIMONE
copy .env.example .env
```

**Eso es todo.** El `.env` trae los valores de desarrollo ya puestos; solo lo
copias. Compruébalo:

```powershell
type .env
```

Debe mostrar `DB_USER=limone_user`, `DB_PASSWORD=limone_password` y
`DB_NAME=limone_db`.

> ⚠️ **Nunca subas `.env` a git.** Está en `.gitignore` a propósito: contiene
> contraseñas. Si algún día lo subes por error, cambia la contraseña antes de
> nada.

Ahora ve a la [sección 4](#4-arrancar-y-parar) y arranca.

### Si quieres usarlo sin Docker

Salta a la [sección 10](#10-modo-local-sin-docker).

---

## 4. Arrancar y parar

### Arrancar

```powershell
docker compose up -d --build
```

Qué hace, en orden:

| # | Paso | Si falla |
|---|---|---|
| 1 | Construye la imagen `limone-app` (~341 MB) | Mira el error del build |
| 2 | Arranca PostgreSQL | — |
| 3 | Espera a que PostgreSQL esté **sano** (`healthcheck`) | La app no arranca, a propósito |
| 4 | Aplica las migraciones de Alembic | La app no arranca, a propósito |
| 5 | Arranca la API con recarga automática | Mira `docker compose logs app` |

El paso 4 y 5 están encadenados en `docker-compose.yml`:

```yaml
command: sh -c "alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
```

**Si una migración falla, la API no arranca.** Es intencional: mejor un error
claro que una base de datos a medias.

### Comprobar que está sano

```powershell
docker compose ps
```

`postgres` debe decir `healthy` y `app` debe decir `running` (o `Up`).

### Parar

```powershell
docker compose stop          # para, conserva los datos y los contenedores
docker compose down          # para y borra los contenedores (los datos SIGUEN)
docker compose down -v       # para y borra TAMBIÉN los datos  <-- destructivo
```

### Reconstruir desde cero

```powershell
docker compose up -d --build
```

Solo hace el build de nuevo si cambiaste algo de la imagen (Dockerfile,
`pyproject.toml`, `uv.lock`). Si solo tocaste código Python, **no hace falta**:
la recarga automática se encarga (sección 8).

---

## 5. Comprobar que funciona

### A. Desde el navegador

Abre **http://localhost:8000/docs**

- `/` redirige solo a `/docs`
- `/docs` — Swagger UI: puedes probar cada endpoint desde ahí
- `/redoc` — la misma API en otro formato

### B. Con la consola de Docker

```powershell
docker compose logs -f app
```

Deberías ver algo como:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

`Ctrl + C` para dejar de mirar los logs (no para la API).

### C. Desde PowerShell

```powershell
# Devuelve la lista en JSON limpio
Invoke-RestMethod http://localhost:8000/lemonades

# Lo mismo, pero con el código de estado a la vista
Invoke-WebRequest http://localhost:8000/lemonades | Select-Object StatusCode, Content
```

> En PowerShell, `curl` es un alias de `Invoke-WebRequest`, no el `curl` de
> Linux. Si vienes de Linux o macOS, `curl http://localhost:8000/lemonades`
> también funciona.

### D. Tres comprobaciones rápidas

```powershell
# 1) Las migraciones están aplicadas
docker compose exec app alembic current

# 2) La tabla existe y tiene datos
docker compose exec postgres psql -U limone_user -d limone_db -c "SELECT count(*) FROM limone;"

# 3) El enum tiene sus 4 valores
docker compose exec postgres psql -U limone_user -d limone_db -c "SELECT unnest(enum_range(NULL::lemonadecategories));"
```

> 💡 **PowerShell pinta en rojo los `INFO` de Alembic y no es un error.**
> Alembic manda sus mensajes a *stderr*, y PowerShell considera stderr como un
> fallo. Fíjate en el final de la línea: si dice `done` o `(head)`, va bien.

---

## 6. Endpoints

Base: `http://localhost:8000`

| Método | Ruta | Qué hace | Código |
|---|---|---|---|
| `POST` | `/lemonades` | Crear una limonada | **201** |
| `GET` | `/lemonades` | Listar todas, ordenadas por id | 200 |
| `GET` | `/lemonades/{id}` | Obtener una por id | 200 / 404 |
| `PUT` | `/lemonades/{id}` | Reemplazar una **completa** | 200 / 404 |
| `PATCH` | `/lemonades/{id}` | Cambiar **solo** los campos que mandes | 200 / 404 |
| `DELETE` | `/lemonades/{id}` | Eliminar | 200 / 404 |

Ningún endpoint recibe filtros ni paginación hoy: `GET /lemonades` devuelve
siempre la lista entera.

### Los tres modelos

Están en `src/models/limone_model.py` y comparten los campos mediante
herencia:

| Modelo | Dónde se usa | Campos |
|---|---|---|
| `Limone` | La tabla (`table=True`) | los 4 + `id` |
| `LimoneCreate` | `POST` y `PUT` | los 4, **todos obligatorios** |
| `LimoneUpdate` | `PATCH` | los 4, **todos opcionales** |

### Ejemplo: crear

`POST /lemonades`

```json
{
  "name": "Limonada Clásica",
  "price": 3500,
  "category": "Classic",
  "flavor": "Limón"
}
```

Respuesta `201 Created`:

```json
{
  "id": 1,
  "name": "Limonada Clásica",
  "price": 3500.0,
  "category": "Classic",
  "flavor": "Limón"
}
```

> `category` solo acepta `"Classic"`, `"Tropical"`, `"Exotic"` o `"Berry"`.
> Cualquier otra cosa devuelve **422** con el detalle de lo que espera. Y ojo
> a las mayúsculas: es `Berry`, no `berry`.

### PUT vs PATCH

| | `PUT` | `PATCH` |
|---|---|---|
| Recibe | **Todos** los campos | Solo los que quieres cambiar |
| Reemplaza | El registro **entero** | Solo lo recibido |
| Modelo | `LimoneCreate` | `LimoneUpdate` |

Ejemplo de `PATCH` (solo cambia el precio):

```json
{ "price": 9500 }
```

El resto de campos se quedan como estaban. Esto es posible gracias a
`model_dump(exclude_unset=True)`: si no mandaste `name`, `name` no aparece y
no se toca.

### Códigos de error que devuelve

| Código | Cuándo | Detalle |
|---|---|---|
| `404` | No existe ese id | `Limonada no encontrada` |
| `409` | Ese nombre ya existe | `La limonada 'X' ya existe` |
| `422` | Validación de FastAPI | campo ausente, tipo incorrecto, enum inválido |
| `422` | Reglas de negocio tuyas | `El precio debe ser mayor que 0` / `El nombre no puede estar vacio` |

El nombre se compara **sin distinguir mayúsculas** (`func.lower`), así que
`Limonada Clasica` y `limonada clasica` chocan con un `409`.

---

## 7. Comandos del día a día

### Docker

| Comando | Qué hace |
|---|---|
| `docker compose up -d --build` | Arrancar todo |
| `docker compose stop` | Parar, conservando todo |
| `docker compose down` | Parar y quitar contenedores (los datos siguen) |
| `docker compose down -v` | **Borrar también los datos** |
| `docker compose ps` | Estado de los servicios |
| `docker compose logs -f app` | Logs de la API en vivo |
| `docker compose restart app` | Reiniciar solo la API |
| `docker compose exec app sh` | Entrar a una consola dentro del contenedor |

### Alembic (siempre dentro del contenedor)

| Comando | Qué hace |
|---|---|
| `docker compose exec app alembic current` | Qué migración está aplicada |
| `docker compose exec app alembic history` | Historial completo |
| `docker compose exec app alembic heads` | La migración más reciente |
| `docker compose exec app alembic upgrade head` | Aplica lo pendiente |
| `docker compose exec app alembic downgrade -1` | Retrocede una migración |

### PostgreSQL (desde tu PC)

| Comando | Qué hace |
|---|---|
| `docker compose exec postgres psql -U limone_user -d limone_db -c "SQL"` | Ejecutar SQL |
| `docker compose exec postgres pg_dump -U limone_user -d limone_db > backup.sql` | Backup |

---

## 8. Cambiar el código

**No hace falta reconstruir nada.** `docker-compose.yml` monta tu carpeta
dentro del contenedor con `--reload`:

```yaml
volumes:
  - .:/app
command: sh -c "... uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
```

El ciclo es este:

1. Editas un archivo (`main.py`, los modelos, etc.).
2. Lo guardas.
3. En la terminal aparece:
   `INFO:     WatchFiles detected changes in 'main.py'. Reloading...`
4. La API se reinicia sola. Sigue en el mismo puerto.

### Cuándo sí hay que reconstruir

| Qué cambiaste | Qué ejecutar |
|---|---|
| Python normal (`main.py`, modelos) | **Nada**, solo guarda |
| `alembic/versions/*` (migración nueva) | `docker compose exec app alembic upgrade head` |
| `Dockerfile` | `docker compose up -d --build` |
| `pyproject.toml` o `uv.lock` | `docker compose up -d --build` |
| `docker-compose.yml` | `docker compose up -d` (o `down` + `up`) |
| `.env` | `docker compose up -d` (las variables se leen al arrancar) |

> **Si no ves el mensaje de recarga**, el archivo probablemente está fuera del
> volumen o no se guardó. Reinicia a mano con `docker compose restart app`.

---

## 9. Migraciones (Alembic)

### Por qué no `create_all`

`SQLModel.metadata.create_all()` **solo crea tablas que no existen**. No sabe
añadir una columna, ni cambiar un tipo, ni borrar nada. Si lo dejas, la primera
vez funciona y a partir de ahí estás bloqueada.

Alembic guarda **cada cambio como un archivo versionado** en
`alembic/versions/`. Así puedes aplicarlo, repetirlo en otra máquina y, si
algo sale mal, retroceder.

### La regla de oro

> **Siempre dentro del contenedor:**
> `docker compose exec app alembic ...`
>
> Para que compare contra **la misma base** a la que se va a aplicar.

### El ciclo completo

**1.** Cambias el modelo en `src/models/limone_model.py`.

**2.** Generas la migración:

```powershell
docker compose exec app alembic revision --autogenerate -m "descripcion clara"
```

**3.** **Lees el archivo generado** en `alembic/versions/`. Siempre. Mira que
no aparezca nada raro (borrar una tabla, por ejemplo).

**4.** La aplicas:

```powershell
docker compose exec app alembic upgrade head
```

**5.** Compruebas:

```powershell
docker compose exec app alembic current
docker compose exec app alembic history
```

### Errores típicos de Alembic

| Mensaje | Causa |
|---|---|
| `Multiple head revisions are present` | Dos migraciones apuntan a la misma madre. Borra una. |
| `Can't locate revision` | El `revision` del archivo está mal. No lo edites a mano. |
| `alembic_version` vacío en `current` | Nunca aplicaste nada: `upgrade head` |

> **`--autogenerate` no lo sabe todo.** Sabe comparar **estructura** (tablas y
> columnas), pero **no** datos: si añades un valor a un Enum, genera una
> migración vacía y no te avisa. Para eso hay que escribirla a mano.
> Lo tienes explicado paso a paso en
> [`guias/03-guia-extra-cambiar-categorias.md`](guias/03-guia-extra-cambiar-categorias.md).

---

## 10. Modo local, sin Docker

Para iterar rápido, con SQLite (un archivo, sin servidor):

```powershell
uv sync                       # instala las dependencias
uv run alembic upgrade head   # crea las tablas (solo la 1ª vez, o si borras limone.db)
uv run uvicorn main:app --reload
```

La API queda en `http://localhost:8000`, igual que con Docker.

### Cómo decide la base qué usar

```
                 ¿Existe DATABASE_URL en el entorno?
                        /                    \
                      SÍ                      NO
                       |                       |
              la usa tal cual          usa sqlite:///./limone.db
```

- **En local:** el `.env` pone `DATABASE_URL=sqlite:///./limone.db`.
- **En Docker:** `docker-compose.yml` define su propio `DATABASE_URL` apuntando
  al servicio `postgres`, y `load_dotenv()` **no sobreescribe** variables que ya
  existen. Así que dentro del contenedor manda el de Docker.

Los dos modos comparten el mismo `alembic/env.py`: cambia solo la URL.

> Ojo: `limone.db` (SQLite) y `limone_db` (PostgreSQL) son **dos bases
> distintas** con sus propios datos. Cambiar de modo no te lleva los datos.

---

## 11. Puertos, variables de entorno y DBeaver

### Puertos

| Puerto | Qué escucha ahí | Quién lo usa |
|---|---|---|
| `8000` | La API | Tu navegador, curl, DBeaver no |
| `5433` | PostgreSQL **desde tu PC** | DBeaver, psql, cualquier cliente |
| `5432` | PostgreSQL **dentro de Docker** | Solo la app, dentro de la red |

> **¿Por qué 5433 y no 5432?** Porque en este equipo ya hay un PostgreSQL
> local de Windows (servicio `postgresql-x64-18`) ocupando el 5432. Se cambió
> solo el de la izquierda en `"5433:5432"`: el de tu PC pasa a 5433, y dentro
> de Docker el servicio sigue escuchando en 5432 y llamándose `postgres`, así
> que la aplicación no se entera.
>
> **No toques el PostgreSQL local de Windows** para este proyecto.

### Variables de entorno

Están en `.env` (copia de `.env.example`):

| Variable | Valor de desarrollo | Para qué |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./limone_db` | Base de datos en modo local |
| `DB_USER` | `limone_user` | Usuario de PostgreSQL |
| `DB_PASSWORD` | `limone_password` | Contraseña |
| `DB_NAME` | `limone_db` | Nombre de la base |

Dentro del contenedor manda el `DATABASE_URL` del `docker-compose.yml`, no el
del `.env` (porque `load_dotenv()` no pisa lo que ya existe).

### Conexión con DBeaver

**Nuevo proyecto de base de datos** → **PostgreSQL**:

| Campo | Valor |
|---|---|
| Server Host | `localhost` |
| Port | **`5433`** ← ojo, no 5432 |
| Database | `limone_db` |
| Username | `limone_user` |
| Password | `limone_password` |
| SSH | sin usar |

Una vez conectada:

```sql
SELECT * FROM limone ORDER BY id;

SELECT unnest(enum_range(NULL::lemonadecategories));

SELECT column_name, data_type, udt_name
FROM information_schema.columns WHERE table_name = 'limone';
```

En esa última consulta verás que `category` es `USER-DEFINED` con
`udt_name = lemonadecategories`: es un tipo Enum **nativo** de PostgreSQL, no
un texto.

> Si DBeaver te rechaza la conexión en el 5433, comprueba con
> `docker compose ps` que el servicio `postgres` está `healthy`. Y si te
> conectas en 5432, estás yendo al PostgreSQL local de Windows, **no** al de
> este proyecto.

---

## 12. Estructura del proyecto

```
LIMONE/
├── main.py                      # La aplicación y los 6 endpoints
├── src/
│   ├── models/
│   │   └── limone_model.py      # Enum, tabla y esquemas de entrada
│   └── shared/
│       └── database/
│           └── session_db.py    # Engine, get_session() y SessionDep
├── alembic/
│   ├── env.py                   # Conexión + autogenerate  <-- el archivo clave
│   ├── script.py.mako           # Plantilla de las migraciones nuevas
│   └── versions/                # Las migraciones, una por cambio
├── alembic.ini                  # Configuración de Alembic
├── guias/                       # Documentación larga, paso a paso
├── Dockerfile                   # Imagen multi-stage con uv
├── docker-compose.yml           # postgres + app, un solo comando
├── pyproject.toml               # Dependencias
├── uv.lock                      # Versión exacta de cada dependencia
├── .env                         # Tus credenciales  (NUNCA se sube a git)
├── .env.example                 # Plantilla sin secretos
└── .gitignore
```

**Dónde mirar según lo que quieras cambiar:**

| Quieres cambiar... | Mira |
|---|---|
| Un endpoint | `main.py` |
| Los campos de los datos | `src/models/limone_model.py` |
| La conexión a la base | `src/shared/database/session_db.py` |
| El esquema de la base | `src/models/...` + una migración nueva |
| Los puertos o servicios | `docker-compose.yml` |
| Las dependencias | `pyproject.toml` (con `uv add <paquete>`) |

---

## 13. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `Bind for 0.0.0.0:5432 failed: port is already allocated` | El PostgreSQL local de Windows ya usa el 5432 | Usa el 5433: ya está así en `docker-compose.yml`. No toques el servicio local |
| `connection refused` al abrir `localhost:8000` | La app no está levantada | `docker compose up -d --build` y mira `docker compose logs app` |
| `FATAL: password authentication failed for user "limone_user"` | Volumen de la base corrupto o de otra instalación | `docker compose down` y luego `docker volume rm limone_postgres_data` (**no** borres `fastapi_luigui_postgres_data`) |
| `no such table: limone` | El esquema no se creó | `docker compose exec app alembic upgrade head` |
| `NameError: name 'sqlmodel' is not defined` | Alembic escribió `AutoString()` sin importarlo | Está corregido en `alembic/env.py` (CAMBIO 3). No lo quites |
| `DuplicateObject: type "lemonadecategories" already exists` | El tipo Enum ya existía al crear la migración | Borra la migración fallida y regenera |
| La API se reinicia en bucle, sin parar | Algo en `--reload` se dispara solo | Suele ser un `.pyc` o un archivo escrito dentro de `/app`. `docker compose restart app` |
| Los datos desaparecen al reiniciar | Falta el volumen o usaste `-v` | `docker compose down -v` **borra los datos**. Para conservarlos, `docker compose stop` |
| `error: failed to solve: ... no such file or directory: uv.lock` | Falta `uv.lock` | `uv sync` en local y vuelve a construir |
| `422` al crear: `Input should be 'Classic', 'Tropical', ...` | `category` no es un texto libre, es un Enum | Usa uno de los 4 valores, con la primera en mayúscula |
| `409`: `La limonada 'X' ya existe` | El nombre ya está usado (sin distinguir mayúsculas) | Cambia el nombre |
| El puerto 8000 ya está ocupado | Otro servidor local (p. ej. la guía 1) | Ciérralo: `Get-NetTCPConnection -LocalPort 8000` y termina ese proceso |
| PowerShell en rojo con `INFO: [alembic...]` | No es un error | Alembic escribe en *stderr*. Mira el final de la línea |

**Diagnóstico rápido:**

```powershell
docker compose ps                          # ¿está sano?
docker compose logs -f app                 # ¿qué dice la app?
docker compose exec app alembic current    # ¿qué migración hay aplicada?
```

---

## 14. Documentación y siguientes pasos

### Las guías

Están en [`guias/`](guias/) y están pensadas para leerse en orden:

| Guía | Qué cubre |
|---|---|
| [`00-conceptos.md`](guias/00-conceptos.md) | El vocabulario: APIs, REST, SQL, Docker, enums, migraciones |
| [`01-guia-crud-fastapi.md`](guias/01-guia-crud-fastapi.md) | Construir el CRUD desde cero con FastAPI y SQLModel |
| [`02-guia-docker-postgres.md`](guias/02-guia-docker-postgres.md) | PostgreSQL, Alembic y Docker: cómo se montó todo esto |
| [`03-guia-extra-cambiar-categorias.md`](guias/03-guia-extra-cambiar-categorias.md) | Cómo cambiar el esquema: añadir categorías y pasar a tabla `categorias` |

### Próximos pasos habituales

- **Añadir un campo nuevo:** modelo → `revision --autogenerate` → leer el
  archivo → `upgrade head` → probar.
- **Añadir un filtro** a `GET /lemonades` (por categoría, por precio).
- **Paginación:** hoy devuelve todo de golpe.
- **Tests:** `pytest` sobre los 6 endpoints.
- **Seguridad:** hoy no hay autenticación ni usuarios.

### Notas para producción

- `echo=True` en `src/shared/database/session_db.py` imprime cada SQL. Sirve
  mientras aprendes; en producción conviene `False`.
- Las credenciales de `.env` son de **desarrollo**. En un servidor real van en
  variables de entorno o en un gestor de secretos, nunca en el repositorio.
- Haz commit pronto: ahora mismo **todo está sin versionar** (`git status`
  muestra los archivos como `??`).
