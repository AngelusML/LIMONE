# Conceptos: el vocabulario que necesitas

Este documento es **solo teoría**. No contiene comandos ni código de tu proyecto.
Su propósito es que entiendas *qué significa* cada cosa antes de empezar a escribir.

**Orden de lectura recomendado:**

| Documento | Qué encontrarás |
|---|---|
| `00-conceptos.md` (este) | El qué y el porqué de cada pieza |
| `01-guia-crud-fastapi.md` | Cómo rehacer tu API de limonadas, paso a paso |
| `02-guia-docker-postgres.md` | Cómo empaquetarlo con Docker y conectar PostgreSQL |

> **Consejo:** este documento está pensado para consultarse muchas veces, no para
> leerlo una sola vez de corrido. Vuelve a la sección que necesites.

---

## PARTE 1 — La web y las APIs

### 1. Cliente y servidor

Casi todo en internet son dos papeles: el que **pide** y el que **responde**.

- **Cliente**: pide. Puede ser tu navegador, una app del celular o un programa.
- **Servidor**: responde. Siempre está encendido, esperando.

Tu proyecto es **el servidor**. Cuando pruebas en `/docs` desde tu navegador, tu
navegador es el cliente y tu computador es el servidor, al mismo tiempo.

**¿Por qué importa?** Porque el servidor no puede saber por su cuenta qué hacer.
Necesita que le lleguen dos cosas: una **petición** que diga qué quieres, y una
**respuesta** que te devuelva el resultado. Todo lo demás son detalles de cómo se
mueven esos dos mensajes.

### 2. API

Una **API** (Application Programming Interface) es la forma en que dos programas
se hablan sin que uno necesite saber cómo está hecho el otro.

**Analogía:** es el **menú de un restaurante**. Tú (el cliente) no entras a la
cocina a cocinar ni ves los ingredientes. Pides platos del menú y te los
traen. El menú es un contrato: te dice qué puedes pedir y qué recibes.

Una API web casi siempre habla **JSON**, que es texto con estructura (lo vemos más
abajo).

### 3. Endpoint o ruta

Un **endpoint** es una dirección concreta que hace una cosa concreta.

```
GET  /lemonades        -> trae TODAS las limonadas
GET  /lemonades/7      -> trae la limonada que tiene el id 7
POST /lemonades        -> crea una limonada nueva
```

La parte que va antes del `/` (por ejemplo `http://localhost:8000`) es
**la base** (el host y el puerto). La parte que empieza en `/` es **la ruta**.

Dentro de la ruta puede haber dos cosas:
- **Verbo** (`GET`, `POST`...): la acción.
- **Parámetro de ruta** (`/lemonades/7`): el `7` es un dato variable que viaja
  dentro de la dirección. En tu código es `limone_id`.

### 4. REST

**REST** es una * convención* (no una tecnología) para designing APIs. Dice:

- Cada cosa es un **recurso** (en tu caso, una `limonada`).
- Cada recurso tiene una **dirección** (en tu caso, `/lemonades`).
- Las acciones se expresan con **verbos estándar**, no con verbos inventados.

Mal diseño (verbos inventados en la URL):

```
GET  /obtenerLimonadas
GET  /crearLimonada
GET  /borrarLimonada?id=5
```

Buen diseño REST (verbos fuera de la URL, recurso limpio):

```
GET    /lemonades
POST   /lemonades
DELETE /lemonades/5
```

**¿Por qué importa?** Porque si sigues la convención, cualquiera (o cualquier
programa) sabe intuitively qué puede hacer con tu API sin leer un manual.

### 5. Los verbos HTTP

Son 5 y cada uno significa algo distinto. Usarlos bien es casi toda la batalla.

| Verbo | Significado | Es idempotente |
|---|---|---|
| `GET` | Leer / consultar. **Nunca** cambia nada. | Sí |
| `POST` | Crear algo nuevo. | No |
| `PUT` | **Reemplazar** un recurso entero. | Sí |
| `PATCH` | **Modificar solo algunas** partes. | No (depende) |
| `DELETE` | Borrar. | Sí |

**Idempotente** significa: si lo ejecutas 1 vez o 5 veces, el resultado final es
el mismo. `DELETE` es idempotente porque borrar algo dos veces termina en
"borrado". Crear algo nuevo 5 veces **sí** crea 5 cosas, por eso `POST` no lo es.

### 6. PUT vs PATCH (la confusión clásica)

Esta es la diferencia que más cuesta, así que la explico con cuidado.

Imagina una ficha de una limonada con 4 campos: nombre, precio, categoría, sabor.

**PUT = "Aquí tienes la ficha completa, reemplaza todo."**

```
PUT /lemonades/7
{ "name": "Limonada", "price": 8000, "category": "Classic", "flavor": "Limón" }
```

Tú tienes que mandar **los 4 campos**. Si mandas solo el nombre, ¿qué pasa con el
precio? Según la estricta definición de PUT, los campos que no mandes se
**borran** (quedan vacíos). Por eso en la práctica casi todos los PUT obligan a
mandar el objeto completo: tu `LimoneCreate` tiene los 4 campos sin opcionales.

**PATCH = "Solo cambia esto, deja el resto como está."**

```
PATCH /lemonades/7
{ "price": 9500 }
```

Solo mandas lo que quieres cambiar. El nombre, la categoría y el sabor se quedan
como estaban. Por eso aquí los campos **deben ser opcionales** (`str | None = None`),
porque no estás obligado a mandar todos.

**Resumen en una línea:**

- `PUT` → necesitas conocer el estado completo del objeto.
- `PATCH` → solo te importa el cambio.

**Por qué es importante entenderlo:** no es solo una cuestión de estilo. Hay
programas (o un celular tuyo) que rely en esta distinción. Si tu `PATCH` termina
borrando los campos que no mandas, cualquier cliente que actualice un solo campo
te va a borrar el resto de la información sin avisar. Es un bug real y silencioso.

### 7. CRUD

**CRUD** son las cuatro operaciones básicas sobre cualquier dato:

| Letra | Nombre | Verbo HTTP |
|---|---|---|
| **C** | Create — Crear | `POST` |
| **R** | Read — Leer | `GET` |
| **U** | Update — Actualizar | `PUT` / `PATCH` |
| **D** | Delete — Borrar | `DELETE` |

Cuando alguien dice "hazme un CRUD", quiere decir exactamente esto: los 4
operaciones sobre un recurso. La guía 2 de este material construye un CRUD
completo de limonadas.

### 8. Códigos de estado

El servidor no devuelve solo datos: devuelve un **número de 3 dígitos** que dice
cómo fue. Ese número va en una línea del HTTP llamada *status*.

Los que vas a usar:

| Código | Significado | Cuándo usarlo |
|---|---|---|
| `200` | OK | Todo salió bien (por defecto en `GET` y `DELETE`). |
| `201` | Created | Se creó algo nuevo. Se usa en `POST`. |
| `404` | Not Found | Pediste algo que no existe. |
| `409` | Conflict | Chocaste con una regla: el nombre ya existe. |
| `422` | Unprocessable Entity | Los datos no tienen sentido (precio negativo, categoría inventada). |
| `500` | Server Error | Se rompió el servidor. Ya no es culpa del que pidió. |

**¿Por qué `422` y no `400`?** `400` significa "la petición está malformada"
(faltó un campo, la sintaxis está rota). `422` significa "la petición está bien
escrita pero su **contenido** no es válido". Lo de Luigi —un precio de `-5`— está
perfectamente bien escrito, solo que no tiene sentido. Por eso `422`.

**Sobre `404` vs `409`:** un `404` es "esto no existe, créalo". Un `409` es "esto
ya existe y no puedo crearlo otra vez". La API de Luigi devuelve `422` para
duplicados; yo uso `409` porque su significado es más exacto. Ambas son
defendibles, lo importante es que seas **consistente**.

### 9. JSON

**JSON** (JavaScript Object Notation) es un formato de texto para exchanging
structured data. Ejemplo de una limonada en JSON:

```json
{
  "id": 1,
  "name": "Limonada Clasica",
  "price": 8000.0,
  "category": "Classic",
  "flavor": "Limon"
}
```

**Dato clave:** entre corchetes `{}` hay **llaves con dos puntos** (la clave y su
valor), los valores van entre comillas si son texto, y termina con coma cada
entrada menos la última. No admite comentarios.

**Conexión con Python:** un `dict` de Python se convierte en JSON y viceversa de
forma casi directa. FastAPI hace esa conversión por ti: tú devuelves objetos de
Python y el cliente recibe JSON.

### 10. UTF-8 y los acentos (Windows)

Un detalle que te va a morder si pruebas con `curl` o PowerShell: los acentos y
la `ñ` son un tema aparte.

`Invoke-RestMethod` de PowerShell a veces manda el cuerpo del POST en una
codificación distinta a UTF-8, y el servidor responde:

```
{"detail":"There was an error parsing the body"}
```

**La solución (PowerShell):** convertir el texto a bytes UTF-8 antes de mandarlo.

```powershell
$json = $obj | ConvertTo-Json -Compress
$bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
Invoke-RestMethod -Uri $url -Method Post -ContentType "application/json; charset=utf-8" -Body $bytes
```

**La solución fácil:** prueba los endpoints desde `/docs` (el navegador), que
maneja UTF-8 correctamente. Guarda esto para cuando pruebes por terminal.

---

## PARTE 2 — FastAPI

### 11. Qué es FastAPI

FastAPI es un **framework web** para Python. Su trabajo: transformar **funciones
de Python** en **endpoints HTTP**.

Lo importante es todo lo que hace *por ti* automáticamente:

1. **Valida** los datos que llegan (tipos, campos obligatorios).
2. **Convierte** tus objetos de Python a JSON.
3. **Genera documentación** interactiva en `/docs` y `/redoc`.
4. **Te dice los errores** de validación con mensajes claros.

**Lo que NO hace por ti:** la lógica de negocio, las reglas (precio > 0, nombre
único) ni talking con la base de datos. Eso lo escribes tú.

### 12. Los decoradores

Una función normal en Python:

```python
def sumar(a, b):
    return a + b
```

En FastAPI le pones un **decorador** encima. El decorador es una función que
envuelve a la tuya y le dice a FastAPI: "esta función responde a esta ruta".

```python
@app.post("/lemonades", status_code=201)
def crear_lemonada(...):
    ...
```

Se lee así: "cuando alguien haga POST a `/lemonades`, ejecuta esta función y
devuelve `201` si todo salió bien".

El decorador es lo que **convierte tu función en un endpoint**. Sin decorador,
es solo una función normal de Python que nadie puede llamar por internet.

### 13. La documentación automática

FastAPI crea solo dos páginas:

- `http://localhost:8000/docs` → **Swagger UI**. Página interactiva donde puedes
  **probar cada endpoint sin escribir nada de código**. Es tu mejor amiga.
- `http://localhost:8000/redoc` → ReDoc. Más bonita, solo para leer.

No necesitas escribir documentación a mano: sale de leer tus propias funciones y
los *type hints* (las anotaciones `-> Limone`, `limone_id: int`). Si no pones
los tipos, la documentación sale vacía y además no hay validación. **Por eso en
tu código siempre hay tipos.**

---

## PARTE 3 — La base de datos

### 14. Base de datos relacional y tablas

Una base de datos guarda información en **tablas**. Una tabla tiene **filas**
(cada cosa que guardas) y **columnas** (cada característica).

Tu tabla `limone`:

```
| id | name                | price | category | flavor |
|----|---------------------|-------|----------|--------|
|  1 | Limonada Clasica    | 8000  | Classic  | Limon  |
|  2 | Limonada Gold       | 15000 | Exotic   | Oro    |
```

**"Relacional"** significa que las tablas pueden relacionarse entre sí (por eso
se llaman "clave foráneas"). **La clave primaria** (`id`) es el identificador
único de cada fila. Nunca se repite y nunca se cambia.

**¿Por qué no usar un Excel?** Porque un Excel no sabe qué campos son obligatorios,
ni qué valores son válidos, ni qué pasa si dos personas escriben a la vez. La base
de datos sí, y por encima se le puede poner permisos y usuarios.

### 15. SQL y los ORM

Para hablar con una base de datos relacional se usa **SQL**, un lenguaje de
consultas:

```sql
SELECT * FROM limone WHERE price > 9000;
```

**ORM** significa *Object-Relational Mapping*: una capa que traduce tus clases de
Python a SQL, para que tú no escribas SQL a mano. SQLModel es un ORM, y también
trae el sistema de validación.

**¿Qué ganas con esto?** El SQL cambia un poco según la base de datos. Con un ORM
escribes Python una vez y funciona en SQLite, en PostgreSQL y en MySQL.

### 16. SQLModel: tabla vs schema

SQLModel te deja definir **dos cosas distintas** que se parecen mucho. Confundirlas
es el error más común:

**1. El modelo tabla** (lo que se guarda en la base de datos):

```python
class Limone(LimoneBase, table=True):   # <-- table=True
    id: int | None = Field(default=None, primary_key=True)
```

- Es la **tabla real**: le dice a la base de datos qué columnas existen.
- **Siempre** lleva el `id` (clave primaria).
- Nunca se usa para "recibir datos del cliente".

**2. Los schemas** (la forma en que viajan los datos por la API):

```python
class LimoneCreate(LimoneBase):    # <-- sin table=True
    pass

class LimoneUpdate(SQLModel):      # <-- sin table=True
    name: str | None = None
```

- Describen **qué campos espera recibir** la API.
- `LimoneCreate`: para `POST` y `PUT`. **Todos los campos obligatorios.**
- `LimoneUpdate`: para `PATCH`. **Todos los campos opcionales**, porque es parcial.
- `Limone` (con `id`): solo para **responder**.

**¿Por qué no usar un solo modelo?** Porque cada operación necesita reglas
distintas. `POST` exige todos los campos, el cliente no puede mandar el `id`
(lo pone la base de datos), y `PATCH` admite campos sueltos. Con un solo modelo
no podrías expresar esas tres cosas a la vez.

`LimoneBase` existe solo para no repetir los 4 campos tres veces. Se llama
**herencia**: la clase hija hereda los campos del padre.

### 17. Enums

Un **enum** (enumeración) es una lista de valores permitidos:

```python
class LemonadeCategories(str, Enum):
    CLASSIC = "Classic"
    TROPICAL = "Tropical"
    EXOTIC = "Exotic"
    BERRY = "Berry"
```

Tu campo `category` no puede ser cualquier texto: tiene que ser uno de esos cuatro.

**¿Por qué es mejor que un texto libre?** Porque si escribes `"clasic"` con error
de tipeo, la validación te lo dice al instante. Con texto libre, guardas "clasic"
en la base de datos y tres meses después nadie sabe qué categoría es.

**Detalle que sorprende (verificado en este proyecto):** PostgreSQL guarda el
enum usando el **nombre** del miembro, en mayúsculas. Si miras la tabla con una
consulta SQL directa verás `CLASSIC` o `TROPICAL`, no `Classic` o `Tropical`. La
API sigue devolviendo `Classic` porque SQLModel convierte al leer. No es un
error; solo tenlo presente si inspeccionas la base de datos a mano.

### 18. Pydantic y la validación

**Pydantic** es la librería que valida que los datos tengan la forma que dices.
FastAPI la usa por ti: si declaras `limone_id: int` y alguien manda
`/lemonades/abc`, la API responde `422` con un mensaje claro sin que escribas
nada.

FastAPI **rechaza** datos inválidos con `422` automáticamente. Pero no sabe nada de
**reglas de negocio** (precio > 0, nombre único). Esas las escribes tú a mano
en la función del endpoint.

### 19. Engine, Session y connection string

Tres piezas que aparecen en `session_db.py`:

**Connection string (URL de conexión)**: es la dirección de tu base de datos, con
usuario y contraseña incluidos.

```
postgresql://limone_user:limone_password@localhost:5432/limone_db
^^^^^^^^^^^    ^^^^^^^^^^    ^^^^^^^^^^^   ^^^^^^  ^^^^^^^   ^^^^^
  motor        usuario      contraseña     host    puerto   base
```

Para SQLite es mucho más corta, porque todo está en un archivo:
`sqlite:///./limone.db`

**Engine**: el objeto que sabe *cómo* hablar con esa base de datos. Lo creas una
sola vez y lo reúses.

**Session**: una "conversación" con la base de datos. Abres una sesión, haces
consultas, y la cierras. `session.add()`, `session.commit()` y `session.delete()`
escriben; `session.exec(select(...))` lee.

**Por qué `commit()` es obligatorio:** mientras no hagas `commit()`, nada está
guardado de verdad. `commit()` es el "ya, guárdalo". `session.refresh()` es para
volver a leer el objeto de la base de datos (por ejemplo, para ver el `id` que la
base de datos le asignó).

### 20. Variables de entorno y secretos

Una **variable de entorno** es un valor que existe solo mientras el programa corre,
 configurable sin tocar el código.

**El `archivo .env`** es un archivo de texto clave=valor que guarda esas
configuraciones. Se carga con `load_dotenv()` y se lee con `os.getenv("NOMBRE")`.

**La regla de oro: las contraseñas NUNCA van escritas en el código.** Van en el
`.env`, y el `.env` nunca se sube a internet. Por eso existe el archivo
`.gitignore` (para Git) y el `.dockerignore` (para Docker), que listing esos
archivos para que no se compartan.

**Detalle que_CONFUSIONA y que verify:**

```python
os.getenv("DATABASE_URL")     # ¿mayúsculas?
os.getenv("Database_url")     # ¿camelCase?
```

En **Windows** los nombres de variables de entorno no distinguen mayúsculas, así
que ambas formas funcionan y nunca notas el problema. En **Linux** (y por lo tanto
en **Docker**) **sí distinguen**, y lo que no coincide **simplemente no existe**.

**Por qué importa mucho:** el proyecto de Luigi tiene su `alembic/env.py` pidiendo
`DATABASE_URL` pero su `.env` definiendo `Database_url`. En su computador
funciona. En Docker se rompe, porque allí es Linux. **No copies eso tal cual**;
usa siempre el mismo nombre, todo en mayúsculas.

### 21. Inyección de dependencias (SessionDep)

Viste esta línea en el código de Luigi:

```python
SessionDep = Annotated[Session, Depends(get_session)]
```

Y luego cada endpoint la usa así:

```python
def crear_lemonada(session: SessionDep):
```

**Qué significa:** en vez de crear la conexión a la base de datos tú mismo dentro
de cada función, le dices a FastAPI "esta función necesita una sesión" y FastAPI
te la pasa.

**`Annotated[...]`** es la forma moderna de decir "este parámetro es de tipo X, y
además necesita Y". (Luigi además importaba `Depends` directo en su `main.py`
sin usarlo; eso es código muerto.)

**¿Por qué es mejor?** Porque la sesión se abre antes de la función y **se cierra
sola después**, aunque la función lance un error. Si tú la abrieras a mano,
olvidarte de cerrarla en algún camino acumularía conexiones abiertas y la
base de datos se caería.

### 22. Migraciones y Alembic

**El problema:** creaste tu tabla con 4 columnas. ¿Cómo la cambias a 5? Si la
modificas "a mano" con una consulta SQL, tu base de datos queda bien pero
*nadie más sabe* que ese cambio existe, y no hay forma de repetirlo en otra
máquina.

**Una migración** es un archivo que describe un cambio en la estructura de la base
de datos, con los comandos exactos para aplicarlo y para deshacerlo.

**Alembic** es la herramienta que genera y aplica migraciones. Con ella:

- Escribes el modelo nuevo en Python.
- Alembic **compara** tu modelo con la base de datos.
- Genera el archivo de migración con el SQL necesario.
- Tú lo revisas (por si acaso) y lo aplicas.

**Versiones:** cada migración tiene un número (por ejemplo `b13caab9b49f`) y sabe
cuál venía antes. Así la base de datos siempre sabe en qué punto está.

**Alternativa simple:** `SQLModel.metadata.create_all(engine)` crea las tablas
que faltan y ya. Es cómodo para empezar, pero no sirve para **cambiar** una tabla
que ya usas: si agregas una columna, `create_all` no la agrega. Por eso en la guía
2 lo usamos (para no complicarte) y en la guía 3 cambiamos a Alembic (que es lo
que se usa en un proyecto real).

---

## PARTE 4 — Docker

### 23. Por qué Docker

**El problema clásico:** "en mi computador funciona". Porque tu Windows tiene un
Python instalado, una versión distinta de cada librería, y el ambiente perfecto.
La persona que corre tu proyecto tiene otra cosa.

**Docker empaqueta todo:** tu código, el Python, las librerías y la configuración
en una sola unidad. Si funciona en Docker, funciona en cualquier lado.

**Analogía:** es como un mudón estanqueado. No importa cómo esté tu cocina de
entrega, el cliente siempre recibe el mismo paquete.

### 24. Imagen vs contenedor

Se confunden todo el tiempo:

- **Imagen**: la "receta", un archivo de instrucciones (el `Dockerfile`). Es
  texto, no se ejecuta.
- **Contenedor**: un contenedor es una **imagen en ejecución**. Puedes tener
  muchos contenedores de la misma imagen (como los "discos" de una copia de
  Windows).

`docker build` crea la imagen. `docker run` / `docker compose up` crea el
contenedor.

### 25. Dockerfile y capas

Un **Dockerfile** es un archivo de texto con instrucciones para construir una
imagen, paso a paso:

```dockerfile
FROM python:3.14-slim
RUN pip install fastapi
COPY . /app
CMD ["uvicorn", "main:app", "--port", "8000"]
```

**Cada instrucción es una "capa".** Docker guarda las capas en caché: si una
capa no cambió, no la vuelve a construir. Por eso el **orden importa**: copia los
archivos de configuración **antes** de copiar tu código. Así si solo cambias
`main.py`, no se reconstruye la capa lenta de instalar librerías.

**Instrucciones clave:**

| Instrucción | Qué hace |
|---|---|
| `FROM` | Sobre qué imagen base construir (por ejemplo `python:3.14-slim`). |
| `RUN` | Ejecuta un comando durante la construcción. |
| `COPY` | Copia archivos de tu proyecto a la imagen. |
| `ENV` | Define una variable de entorno. |
| `WORKDIR` | Define la carpeta de trabajo. |
| `EXPOSE` | Documenta qué puerto usa la app. |
| `CMD` | Qué ejecutar cuando arranque el contenedor. |
| `USER` | Con qué usuario corre. **No uses `root`.** |

### 26. Puertos y mapeo

Dentro de un contenedor, tu app escucha en el puerto `8000` **por dentro**.

Tu computador tiene sus propios puertos, y el `8000` de tu computador es
**otro** `8000` que el del contenedor.

El mapeo traduce entre los dos:

```yaml
ports:
  - "8000:8000"     # TU computador : DENTRO del contenedor
```

Teajes acceden a `http://localhost:8000`, Docker lo pasa al `8000` de dentro.

Y aquí está el error **más común** de todo Docker:

```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

Significa: **ya hay algo usando el puerto 5432 en tu computador**. Puede ser otro
contenedor tuyo de un intento anterior, o un PostgreSQL instalado
nativamente. **Solución:** o liberas el puerto, o usas otro:
`"5433:5432"` (5433 en tu computador, 5432 dentro). Lo del lado derecho
**déjalo siempre igual** (5432), porque es el puerto interno de PostgreSQL.

### 27. Volúmenes

Un contenedor es **desechable**: si lo borras, se pierde todo lo que tenía
dentro. Eso está bien para tu código, pero **no para tu base de datos**.

Un **volumen** es un espacio de disco que sobrevive a los contenedores. En el
compose:

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

Significa: guarda los datos de PostgreSQL en el volumen `postgres_data` en vez de
adentro del contenedor.

Si necesitas **borrar todo desde cero** (empezar de nuevo), el volumen es lo
primero que se destruye:

```bash
docker compose down -v
```

### 28. docker-compose.yml

Un **servicio** es un contenedor dentro de tu compose. Un `docker-compose.yml`
los describe todos y los levanta **juntos**, en el orden correcto y conectados
por una red privada.

Tú tienes **dos servicios**: `postgres` (la base de datos) y `app` (tu API).

**Red privada:** dentro de compose, un servicio alcanza a otro por su **nombre**.
Por eso la URL de la base de datos, dentro de Docker, es
`postgresql://usuario:clave@postgres:5432/base` — `postgres` es el nombre del
servicio.

**Ese es otro error clásico:** si pones `localhost` dentro de Docker, no
encontrarás la base de datos, porque `localhost` dentro del contenedor es **el
propio contenedor**, no tu computador. Fuera de Docker sí es `localhost`.

### 29. Healthcheck y depends_on

Levantar cosas al mismo tiempo tiene un problema: la app puede intentar
conectarse a PostgreSQL antes de que esté listo, fallar, y morirse.

**Solución: `healthcheck`.** Es una pregunta de salud que Docker le hace al
contenedor cada pocos segundos:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
  interval: 5s
  timeout: 5s
  retries: 5
```

Y **`depends_on`** le dice a la app: "no arranques hasta que postgres esté
*healthy*":

```yaml
depends_on:
  postgres:
    condition: service_healthy
```

Con esto, al hacer `docker compose up -d` verás en la salida:

```
Container limone_postgres Healthy
Container limone_app Starting
```

Ese orden en la salida es la prueba de que funcionó. (Luigi lo tiene igual:
`condition: service_healthy`. Esta parte la copiamos tal cual, porque está bien
hecha.)

### 30. Multi-stage build

**El problema:** para instalar librerías necesitas herramientas de compilación
grandes. Un `python:slim` sin ellas no las tiene. Pero esas herramientas no
deberían estar en la imagen final: ocupan espacio y son un riesgo de seguridad.

**Solución: multi-stage build.** Divides el `Dockerfile` en etapas:

- **Etapa 1 (builder)**: la imagen grande, con compilador. Instala todo.
- **Etapa 2 (final)**: la imagen pequeña. Solo copia el resultado.

```
FROM uv:python3.14 AS builder     <- grande, instala
   ...uv sync...
FROM python:3.14-slim             <- pequeña, solo recibe
   COPY --from=builder /app/.venv /app/.venv
```

Este patrón **copiaba exactamente el de Luigi**, y el nombre de su builder
`ghcr.io/astral-sh/uv:python3.12-bookworm-slim` es la imagen oficial de `uv` ya
con Python instalado. En la guía 3 usamos la versión 3.14 equivalente.

**Extra: usuario sin privilegios.** En la etapa final Luigi crea un usuario
`appuser` y le da `USER appuser`. Tu app no necesita ser root, y si alguien logra
inyectarle código, no tendrá el control total de la máquina. Es buena práctica y
gratis.

---

## PARTE 5 — `uv` y el entorno virtual

### 31. El problema: las librerías se chocan

Cada proyecto usa versiones distintas de las mismas librerías. Si el proyecto A
necesita FastAPI 0.100 y el proyecto B necesita 0.141, no pueden vivir juntos en
la misma instalación de Python.

### 32. El entorno virtual

Un **entorno virtual** (venv) es una carpeta con su propia copia de Python y sus
propias librerías, aislada del resto. Cada proyecto tiene el suyo.

Al ejecutar algo dentro del venv, solo ve lo que está ahí dentro.

El tuyo se llama `.venv` (con punto al inicio, por convención). Es simplemente
una carpeta: puedes borrarla entera y recrearla sin perder nada.

### 33. uv, y por qué Luigi lo usa

**`uv`** es un gestor de dependencias y entornos written en Rust. Frente a
`pip`:

| | `pip` | `uv` |
|---|---|---|
| Velocidad | Lento | Mucho más rápido (10-100x) |
| Entorno virtual | `python -m venv` aparte | Crea él mismo con `uv sync` |
|archivo de versiones | No automáticamente | `uv.lock`, exacto |

**`uv sync`** hace tres cosas de una: crea/actualiza el venv, instala lo que dice
`pyproject.toml`, y respeta el `uv.lock`. Es el único comando que necesitas para
dejar un proyecto andando.

**Regla importante:** siempre ejecuta los comandos con `uv run`. Así se usa el
entorno virtual del proyecto, no el Python global de tu computador.

```
uv run alembic upgrade head
uv run uvicorn main:app --reload
```

### 34. pyproject.toml y uv.lock

**`pyproject.toml`** es la "carta" del proyecto: cómo se llama, qué versión de
Python necesita y qué librerías requiere. Es un archivo de texto.

```toml
dependencies = [
    "fastapi[standard]>=0.141.1",
    "sqlmodel>=0.0.46",
    "python-dotenv>=1.2.3",
]
```

**`uv.lock`** es el archivo generado que fija **la versión exacta** de cada
librería y de sus dependencias. Se genera con `uv lock` y se sube al repositorio.

**¿Por qué los dos?** `pyproject.toml` dice "quiero SQLModel 0.0.46 o superior" (lo
que tú pediste). `uv.lock` dice "instalé 0.0.46 con estas 52 versiones exactas" (lo
que quedó instalado). Tu compañero y tú, con el mismo lock, instaláis
**exactamente lo mismo**. Es la diferencia entre "en mi Computador funciona" y
"funciona en todas partes".

**Un detalle del proyecto de Luigi que te va ayeri bien:** su `pyproject.toml`
**no tiene sección `[build-system]`**, y por eso sus comandos usan
`--no-install-project`. Tu proyecto actual **sí** la tiene, y por eso tiene esa
carpeta rara `src/limone/` que no hace nada. Esa carpeta existe únicamente
porque esa sección dice que el proyecto es un paquete instalable. La guía 2 lo
limpia.

---

## RESUMEN EN UNA PÁGINA

```
Cliente (navegador)  --petición HTTP-->  Servidor (tu API)
                                              |
                              FastAPI: valida y documenta
                                              |
                                  Session: habla con
                                              |
                                    Base de datos
```

| Pieza | Qué hace | Dónde vive |
|---|---|---|
| **Endpoint** | Una dirección + verbo que hace algo | `main.py` |
| **Modelo tabla** | Las columnas de la base de datos | `src/models/limone_model.py` |
| **Schemas** | Qué datos espera/entrega la API | `src/models/limone_model.py` |
| **Session** | Conversación con la base de datos | `src/shared/database/session_db.py` |
| **Engine** | Cómo hablarle a la base de datos | `src/shared/database/session_db.py` |
| **Variables de entorno** | Configuración y secretos | `.env` |
| **Imagen** | Receta empaquetada (texto) | `Dockerfile` |
| **Contenedor** | Imagen corriendo | `docker compose up` |
| **Volumen** | Datos que sobreviven al contenedor | `docker-compose.yml` |

---

## Glosario inglés ↔ español

| Inglés | Español | Dónde lo ves |
|---|---|---|
| endpoint / route | ruta | `POST /lemonades` |
| request / response | petición / respuesta | HTTP |
| payload / body | cuerpo | los datos que mandas |
| query | consulta | `select(...)` |
| model | modelo | `class Limone` |
| schema | esquema | `LimoneCreate` |
| field | campo | `name: str` |
| table | tabla | `limone` |
| row | fila | una limonada |
| column | columna | `price` |
| primary key | clave primaria | `id` |
| session | sesión | `Session(engine)` |
| engine | motor | `create_engine(...)` |
| connection string | cadena de conexión | `DATABASE_URL` |
| commit | confirmar | `session.commit()` |
| refresh | recargar | `session.refresh()` |
| dependency injection | inyección de dependencias | `SessionDep` |
| migration | migración | `alembic/versions/` |
| upgrade / downgrade | aplicar / revertir | `alembic upgrade` |
| image | imagen | `Dockerfile` |
| container | contenedor | `docker run` |
| build | construir | `docker build` |
| volume | volumen | `postgres_data` |
| service | servicio | `postgres`, `app` |
| healthcheck | verificación de salud | `pg_isready` |
| environment variable | variable de entorno | `.env` |
| secret | secreto | contraseña |
| dependency | dependencia | librería |
| virtual environment | entorno virtual | `.venv` |

---

## Autoevaluación

Antes de pasar a la guía 2, deberías poder responder esto sin mirar:

1. ¿Cuál es la diferencia entre `PUT` y `PATCH`? Dame un ejemplo.
2. ¿Por qué tu `Limone` tiene `id` pero tu `LimoneCreate` no?
3. ¿Qué es `commit()` y qué pasa si no lo llamas?
4. Si `POST` recibe `price: -5`, ¿qué código debería responder y por qué no
   400 sino 422?
5. ¿Por qué tu `.env` nunca se sube a Git?
6. ¿Qué es `SessionDep` y qué problema resuelve?
7. En Docker, ¿por qué la base de datos se llama `postgres` y no `localhost`?
8. ¿Qué significa "multi-stage build" y qué problema resuelve?
9. ¿Cuál es la diferencia entre una imagen y un contenedor?
10. ¿Por qué `uv.lock` va en el repositorio pero `.env` no?

Si alguna no la sabes, vuelve a la sección correspondiente. Es el punto exacto
donde te vas a atascar después, así que mejor verlo ahora.
