# Guía extra: cambiar las categorías (Enum → tabla)

Esta guía es un **complemento** de la guía 2. No la sustituye: la guía 2 te
enseñó a crear la tabla desde cero; esta te enseña a **cambiarla cuando ya
existe**, que es lo que de verdad pasa en un proyecto real.

**Antes de empezar:** termina la guía 2 y confirma que todo funciona con
`docker compose up -d --build`.

> **Aviso honesto sobre lo que está probado.** Las piezas de esta guía salen
> de fuentes verificadas en este ordenador: el código real de Alembic
> instalado (el `autocommit_block` viene de su propia documentación, en
> `alembic/runtime/migration.py`), tu primera migración real
> (`alembic/versions/ae4e3b224752_crear_tabla_limone.py`), tu base de datos
> (`PostgreSQL 16.15`), y los comandos que ya usaste en la guía 2. Lo que
> **no** he hecho es ejecutar las migraciones de esta guía contra una base de
> datos de prueba, así que trata cada paso como una receta que vas a comprobar
> tú misma con los comandos de verificación que verás. Cada parte termina con
> su checklist precisamente para eso.

---

## Qué vas a entender aquí

| | **Parte A** | **Parte B** |
|---|---|---|
| **Qué haces** | Añadir una categoría al Enum | Dejar el Enum y pasar a una tabla `categorias` |
| **Coste por cambio** | Una migración cada vez | Un `INSERT`, sin migración |
| **Cuándo te sirve** | Cambios ocasionales | Vas a crecer (agua, pasabocas, pasteles) |
| **Dificultad** | Fácil | Media |

**Regla rápida:** si vas a añadir categorías más de dos o tres veces, no
amplíes el Enum: pasa directo a la **Parte B**.

---
---

# PARTE A — Añadir una categoría tú misma

## A.1 Qué es lo que vas a cambiar

Un Enum es una **lista cerrada**. Ahora mismo tu lista es:

```python
class LemonadeCategories(str, Enum):
    CLASSIC  = "Classic"
    TROPICAL = "Tropical"
    EXOTIC   = "Exotic"
    BERRY    = "Berry"
```

Por eso tu primer POST falló con `Input should be 'Classic', 'Tropical',
'Exotic' or 'Berry'`. No era un bug: la API estaba haciendo su trabajo.

Añadir `Cereza` no es un cambio de texto: **es cambiar el tipo de la columna
en PostgreSQL**, y eso siempre va con migración.

## A.2 El truco que lo explica todo: nombre vs valor

Cada línea tiene **dos textos**, y viven en sitios distintos:

| Parte | Ejemplo | Quién lo ve |
|---|---|---|
| Izquierda — el **nombre** | `CLASSIC` | **La base de datos** |
| Derecha — el **valor** | `"Classic"` | **La API y el cliente** |

Compruébalo tú misma en DBeaver (o desde la terminal):

```powershell
docker compose exec postgres psql -U limone_user -d limone_db -c "SELECT unnest(enum_range(NULL::lemonadecategories));"
```

```
  valor
----------
 CLASSIC
 TROPICAL
 EXOTIC
 BERRY
(4 rows)
```

La base guarda `CLASSIC` (el nombre, en mayúsculas). La API te devuelve
`"Classic"` (el valor).

**Esta es la parte que más se olvida:** cuando añadas una categoría, en SQL
tendrás que usar el **nombre** (`'CEREZA'`), y en el JSON de la API el
**valor** (`"Cereza"`).

---

## A.3 Paso 1 — Edita el modelo

Abre `src/models/limone_model.py` y añade **una línea** dentro del Enum:

```python
class LemonadeCategories(str, Enum):
    CLASSIC  = "Classic"
    TROPICAL = "Tropical"
    EXOTIC   = "Exotic"
    BERRY    = "Berry"
    CEREZA   = "Cereza"   # <--- nueva
```

Guarda el archivo. Gracias al volumen de `docker-compose.yml` y al `--reload`,
la app se recarga sola. Compruébalo en la terminal: deberías ver algo como
`WatchFiles detected changes in 'src/models/limone_model.py'`.

> **Si no te aparece el mensaje de recarga:** la app no está mirando ese
> archivo, o la has editado fuera del volumen. Reinicia con
> `docker compose restart app`.

---

## A.4 Paso 2 — Crea el archivo de migración **en blanco**

```powershell
docker compose exec app alembic revision -m "anadir categoria Cereza"
```

> ⚠️ **Ojo con el `--autogenerate`.** Si lo añades, te genera una migración
> **vacía** y lo peor es que no te avisa. Lo comprobé en el Alembic
> instalado: su comparador **no revisa los valores de un Enum**, solo el tipo
> de la columna. Como el tipo sigue llamándose `lemonadecategories`, Alembic
> cree que "no ha cambiado nada".
>
> Con `alembic revision` (sin `--autogenerate`) Alembic solo crea el archivo
> con la estructura vacía, y ahí escribes tú a mano qué quieres hacer. Es el
> caso de uso correcto: **tú sabes mejor que Alembic qué cambió.**

Salida esperada:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
  Generating /app/alembic/versions/anadir_categoria_cereza.py ... done
```

> **PowerShell lo pinta en rojo y no es un error.** Alembic manda sus
> mensajes `INFO` a **stderr**, y PowerShell considera stderr como un fallo.
> Fíjate en que acaba en `... done`. Si el archivo apareció en
> `alembic/versions/`, todo va bien.

El archivo aparece en `alembic/versions/` con un nombre parecido a
`anadir_categoria_cereza.py`. Ábrelo. Verás esto (con tus IDs y fechas):

```python
"""anadir categoria Cereza

Revision ID: abc123def456
Revises: ae4e3b224752
Create Date: 2026-09-28 ...

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: Union[str, Sequence[str], None] = 'ae4e3b224752'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
```

**No toques los IDs** (`revision`, `down_revision`...). Los pone Alembic y son
la que marca tu lugar en el historial. Lo único que vas a escribir es el
contenido de `upgrade()` y `downgrade()`.

> Comprueba que `down_revision` es `ae4e3b224752`. Si tienes duda, corre
> `docker compose exec app alembic heads` — te enseña la revisión que está
> en la punta, y esa es la que debe ser tu padre.

---

## A.5 Paso 3 — Escribe `upgrade()` y `downgrade()`

Reemplaza las dos funciones por esto:

```python
def upgrade() -> None:
    """Upgrade schema."""
    # PostgreSQL exige que ALTER TYPE ... ADD VALUE se ejecute FUERA de una
    # transaccion. Alembic corre cada migracion dentro de una, asi que hay
    # que salirse explicitamente con autocommit_block().
    # (Este ejemplo viene de la documentacion de Alembic, alembic/runtimemigration.py)
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE lemonadecategories ADD VALUE IF NOT EXISTS 'CEREZA'"
        )


def downgrade() -> None:
    """Downgrade schema."""
    # OJO: PostgreSQL 16 NO permite borrar un valor de un Enum. Esa
    # funcion, ALTER TYPE ... DROP VALUE, llego en PostgreSQL 17.
    # Tu contenedor usa postgres:16-alpine.
    # Si esto devolviera "pass", Alembic diria "ya estas en la version
    # anterior" pero el valor CEREZA seguiria en la base: una mentira.
    # Fallar en alto es mejor que mentir.
    raise NotImplementedError(
        "PostgreSQL 16 no permite ALTER TYPE ... DROP VALUE. "
        "Mira la seccion A.6.1 para deshacerlo a mano."
    )
```

Tres detalles que importan:

| Detalle | Por qué |
|---|---|
| `autocommit_block()` | Sin esto, PostgreSQL devuelve `unsafe use of new value` |
| `IF NOT EXISTS` | Te deja correr la migración dos veces sin que reviente |
| `'CEREZA'` en mayúsculas | La base guarda el **nombre**, no el valor |

### A.6.1 Por si necesitas deshacerlo (avanzado)

`alembic downgrade -1` va a fallar a propósito, como viste arriba. Si de
verdad necesitas quitar el valor, en PostgreSQL 16 hay que **recrear el tipo
entero**. Esto es destructivo si se hace mal, así que **haz backup primero**:

```powershell
docker compose exec postgres pg_dump -U limone_user -d limone_db > backup_antes_de_deshacer.sql
```

Luego, en DBeaver, en este orden exacto:

```sql
-- 1. Pasar la columna a texto para que deje de depender del Enum
ALTER TABLE limone ALTER COLUMN category TYPE text USING category::text;

-- 2. Borrar el tipo (ahora ya nadie lo usa)
DROP TYPE lemonadecategories;

-- 3. Recrearlo SIN el valor que quieres quitar
CREATE TYPE lemonadecategories AS ENUM ('CLASSIC', 'TROPICAL', 'EXOTIC', 'BERRY');

-- 4. Volver al Enum
ALTER TABLE limone ALTER COLUMN category TYPE lemonadecategories
    USING category::lemonadecategories;
```

Si el paso 2 te da `ERROR: type "lemonadecategories" is used by a column`,
es que olvidaste el paso 1 o hay otra columna usando el tipo:

```sql
-- ¿Quién más usa este tipo?
SELECT table_name, column_name
FROM information_schema.columns
WHERE udt_name = 'lemonadecategories';
```

---

## A.6 Paso 4 — Aplica la migración

```powershell
docker compose exec app alembic upgrade head
```

Salida esperada:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade ae4e3b224752 -> abc123def456, anadir categoria Cereza
```

**Comprueba las tres cosas:**

```powershell
docker compose exec app alembic current
```
```
abc123def456 (head)
```

```powershell
docker compose exec app alembic history
```
```
ae4e3b224752 -> abc123def456 (head), anadir categoria Cereza
```

```powershell
docker compose exec postgres psql -U limone_user -d limone_db -c "SELECT unnest(enum_range(NULL::lemonadecategories));"
```
```
  valor
----------
 CLASSIC
 TROPICAL
 EXOTIC
 BERRY
 CEREZA
(5 rows)
```

Si aparece `CEREZA`, **ya está en la base de datos**. Ahora al modelo.

---

## A.7 Paso 5 — Prueba la API

Abre `http://localhost:8000/docs` y manda un **POST** a `/lemonades`:

```json
{
  "name": "Limonada de Cereza",
  "price": 10000,
  "category": "Cereza",
  "flavor": "Cereza"
}
```

> Fíjate: en el JSON va el **valor** `Cereza` (con mayúscula inicial), no
> `CEREZA`.

Esperas `201 Created`. Y ahora verifica qué guardó **realmente** la base:

```powershell
docker compose exec postgres psql -U limone_user -d limone_db -c "SELECT id, name, price, category FROM limone ORDER BY id DESC LIMIT 1;"
```

| Columna | Verás | ¿Por qué? |
|---|---|---|
| `name` | `Limonada de Cereza` | Tal cual lo mandaste |
| `category` | `CEREZA` | La base guarda el **nombre** del Enum |

Ese `CEREZA` en mayúsculas **es correcto**, no lo "arregles".

---

## A.8 Errores reales de la Parte A

### 1. `unsafe use of new value "CEREZA" of enum type "lemonadecategories"`

**Causa:** usaste el valor nuevo en la misma transacción en la que lo
creaste. Suele pasar si escribes el `ADD VALUE` y un `INSERT` con `CEREZA`
en el mismo bloque, o si quitaste el `autocommit_block()`.

**Solución:** vuelve al código de la sección A.5. El `ADD VALUE` tiene que ir
dentro de `with op.get_context().autocommit_block():`.

### 2. `type "lemonadecategories" does not exist`

**Causas posibles:**
- Error de tipeo en el nombre del tipo.
- Estás corriendo contra **SQLite** (modo local). SQLite no tiene tipos Enum:
  mira tu `.env` y confirma que `DATABASE_URL` apunta a PostgreSQL.
- La migración 1 (`crear tabla limone`) nunca se aplicó.

**Comprobación:**

```powershell
docker compose exec app alembic current
```
Debe decir `ae4e3b224752` o superior. Si está vacío, la base no tiene esquema.

### 3. `Multiple head revisions are present`

**Causa:** creaste dos migraciones en blanco con el mismo `down_revision`
(olvídate de la anterior y volviste a ejecutar `alembic revision`).

**Comprobación y arreglo:**

```powershell
docker compose exec app alembic heads
```

Si salen dos, borra el archivo que no vas a usar de `alembic/versions/` y
vuelve a comprobar con `docker compose exec app alembic history`.

### 4. El POST sigue dando 422 con `Input should be 'Classic', 'Tropical', 'Exotic' or 'Berry'`

**Causa:** la app no recargó con tu cambio del Enum.

**Solución:**
1. Comprueba que guardaste `src/models/limone_model.py`.
2. Mira la terminal: debe salir el mensaje de `WatchFiles`.
3. Si no sale, `docker compose restart app`.

> Ojo: si reiniciaste con `restart` y **antes** no habías aplicado la
> migración, verás `UndefinedColumn` o `InvalidEnumValue`. Son dos problemas
> distintos: modelo sin guardar, o migración sin aplicar.

### 5. Todo en rojo pero `... done`

**No es un error.** Alembic manda sus `INFO` a stderr y PowerShell lo pinta
en rojo. Mira el final de la línea: si dice `done`, y el archivo apareció en
`alembic/versions/`, vas bien. Lo compruebas con
`docker compose exec app alembic history`.

### 6. `Error response from daemon: No such container: ...`

**Causa:** el proyecto no está levantado.

**Solución:**

```powershell
docker compose up -d --build
```

### 7. `alembic current` no muestra tu nueva revisión

**Causa:** no aplicaste la migración, o te equivocaste copiando la
`revision` a mano (por eso dije que no la tocaras).

**Comprobación:**

```powershell
docker compose exec app alembic history
docker compose exec app alembic current
```

`history` enseña las migraciones **que existen**; `current` enseña las que
**ya se aplicaron**. Si aparece en una y no en la otra, vuelve a correr
`docker compose exec app alembic upgrade head`.

---

## A.9 Checklist de la Parte A

### Modelo
- [ ] Añadí la línea nueva dentro de `LemonadeCategories`
- [ ] Vi el mensaje de `WatchFiles` en la terminal

### Migración
- [ ] Creé el archivo con `alembic revision` **sin** `--autogenerate`
- [ ] `down_revision` es `ae4e3b224752`
- [ ] `upgrade()` usa `autocommit_block()`
- [ ] El valor en SQL va en mayúsculas: `'CEREZA'`
- [ ] `downgrade()` lanza `NotImplementedError`

### Aplicación
- [ ] `alembic upgrade head` terminó sin errores
- [ ] `alembic current` muestra mi nueva revisión como `(head)`
- [ ] `enum_range` devuelve 5 valores

### API
- [ ] El POST con `"category": "Cereza"` devuelve `201`
- [ ] En DBeaver, `category` aparece como `CEREZA`

---
---

# PARTE B — Dejar el Enum y pasar a una tabla `categorias`

## B.0 Por qué el Enum te va a frenar

Con el Enum, cada categoría nueva es: editar Python → crear migración →
escribirla a mano → aplicarla → desplegar. Con una tabla, es una línea:

```sql
INSERT INTO categorias (nombre) VALUES ('Agua');
```

Piensa en lo que vas a vender: limonadas, agua, pasabocas, deditos, pasteles.
¿Cuántas categorías son? ¿Y las que se te ocurran dentro de dos meses? Con
Enum, cada una es una migración y un despliegue. Con tabla, es un
`INSERT` que puedes hacer desde DBeaver en cinco segundos.

**Este es el momento de cambiar**, y aprovechas que todavía tienes poquitos
datos.

### A/B: ¿cuándo usar cada uno?

| Situación | Usa |
|---|---|
| Lista cerrada que casi no cambia (sí/no, estados de un pedido) | Enum |
| Lista que crece: categorías, etiquetas, proveedores | **Tabla + FK** |
| Cada tipo de producto tiene campos muy distintos | Tabla por tipo (todavía no lo necesitas) |

---

## B.1 El modelo nuevo

```
categorias
-----------
id          integer   PRIMARY KEY
nombre      varchar   NOT NULL  UNIQUE

limone   (en el futuro: "productos")
-----------
id            integer   PRIMARY KEY
name          varchar   NOT NULL
price         float     NOT NULL
flavor        varchar   NOT NULL
category      Enum      NOT NULL   <-- se BORRA
categoria_id  integer   NOT NULL   --> categorias.id   <-- se AÑADE
```

Notas:

- **`UNIQUE` en `nombre`**: para que no puedas tener dos categorías "Agua".
- **`categoria_id` con clave foránea**: PostgreSQL no te deja guardar un
  `categoria_id` que no exista en `categorias`. Esa garantía es justo lo que
  ganas.
- **Los nombres se quedan como están.** La tabla sigue llamándose `limone`,
  y las columnas siguen siendo `name`, `price` y `flavor` — no `nombre` ni
  `precio`. Renombrar toca `main.py` y todos tus endpoints: no lo mezcles
  con este cambio. Hazlo en otra migración (lo tienes en B.7).

---

## B.2 Paso 1 — Cambia el modelo de Python

En `src/models/limone_model.py`, añade la clase `Categoria` y cambia el
campo `category` de `LimoneBase`:

```python
class Categoria(SQLModel, table=True):
    __tablename__ = "categorias"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True)
```

Y dentro de `LimoneBase`, **sustituye** la línea de `category`:

```python
# ANTES
category: LemonadeCategories

# DESPUES
categoria_id: int = Field(foreign_key="categorias.id")
```

> **`__tablename__` explícito.** Es opcional (SQLModel lo deduce de la clase),
> pero ponerlo a mano evita sorpresas con la clave foránea: el texto
> `"categorias.id"` tiene que coincidir **exactamente** con el nombre de la
> tabla.

Borra también la clase `LemonadeCategories` cuando ya no la use nadie — pero
**no la borres todavía**: la necesitas durante la migración para leer los
datos viejos. Bórrala en un paso aparte, después de aplicar todo.

Guarda. **La app va a fallar al recargar** porque en la base de datos todavía
no existe `categoria_id`. Es esperado: no te asustes, en el paso siguiente
arreglas la base. Si te molesta ver el error en la terminal, párala con
`docker compose stop app` y levántala al final.

---

## B.3 Paso 2 — Genera la migración y **siéntate a leerla**

```powershell
docker compose exec app alembic revision --autogenerate -m "categorias con fk"
```

Esta vez **sí** usamos `--autogenerate`: aquí Alembic sí sabe comparar
(puede ver una columna nueva y una tabla nueva).

Abre el archivo generado y **búscale las cuatro cosas**. Esto es lo que va a
importar de verdad:

| # | ¿Qué buscas? | ¿Está? | Qué hacer |
|---|---|---|---|
| 1 | `op.create_table('categorias', ...)` | Sí | Déjalo |
| 2 | `op.add_column('limone', ... categoria_id ...)` y la clave foránea | Sí | Déjalo, **pero mira el paso B.4** |
| 3 | `op.drop_column('limone', 'category')` | Tal vez | Si está, **necesitas la migración de datos ANTES**. Ver B.5 |
| 4 | Los `INSERT` con tus 4 categorías | **Nunca** | Hay que escribirlos a mano. Ver B.4 |

**La lección de fondo:** Alembic compara *estructura*, no *datos*. Sabe que
falta una tabla; **no sabe** que tienes cuatro categorías metidas en un Enum
esperando a ser volcadas. Esa parte es siempre tuya.

> ⚠️ **Peligro máximo — revisa que NO aparezca `op.drop_table('limone')`.**
> Si lo ves, **no lo apliques**: borraría tu tabla con todos los datos.
> Los `--autogenerate` no detectan renombres de tabla; si cambias
> `__tablename__`, Alembic ve "borrar una, crear otra". Nunca aceptes un
> `drop_table` en una migración que lleva datos. (De hecho, por eso en B.1
> te dije que **no** renombraras nada todavía.)

---

## B.4 Paso 3 — Escribe a mano el volcado de datos

Esta es la parte que nunca te hace Alembic. Reemplaza `upgrade()`:

```python
def upgrade() -> None:
    """Upgrade schema."""
    # ---------------------------------------------------------------
    # 1. Crear la tabla nueva (lo genero Alembic, lo dejo igual)
    # ---------------------------------------------------------------
    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )

    # ---------------------------------------------------------------
    # 2. Añadir la columna SIN restriccion NOT NULL todavia.
    #    Si la pones NOT NULL ahora, PostgreSQL responde:
    #        ERROR: column "categoria_id" contains null values
    #    porque la tabla "limone" ya tiene filas y esas filas no
    #    tienen categoria_id. Se arregla en el paso 4.
    # ---------------------------------------------------------------
    op.add_column(
        "limone",
        sa.Column("categoria_id", sa.Integer(), nullable=True),
    )

    # ---------------------------------------------------------------
    # 3. VOLCAR LOS DATOS. Lo que Alembic nunca escribe.
    #
    #    La primera linea copia los valores del Enum (CLASSIC, TROPICAL,
    #    EXOTIC, BERRY) a filas de la tabla nueva, sin escribirlos a mano:
    #    enum_range() te devuelve justo los valores que hay hoy.
    #
    #    La segunda linea rellena categoria_id en cada fila existente,
    #    casando el nombre de la categoria con el valor del Enum.
    #    Los dos textos coinciden exactamente porque enum_range() devuelve
    #    el NOMBRE, que es lo que esta guardado en la columna.
    # ---------------------------------------------------------------
    op.execute(
        "INSERT INTO categorias (nombre) "
        "SELECT unnest(enum_range(NULL::lemonadecategories))"
    )
    op.execute(
        "UPDATE limone SET categoria_id = categorias.id "
        "FROM categorias "
        "WHERE categorias.nombre = limone.category::text"
    )

    # ---------------------------------------------------------------
    # 4. AHORA SI: obligar a que categoria_id tenga valor.
    #    Si cualquier fila sigue en NULL, esto falla. En ese caso el
    #    error te dice exactamente que el volcado no cubrio todas las
    #    categorias.
    # ---------------------------------------------------------------
    op.execute("ALTER TABLE limone ALTER COLUMN categoria_id SET NOT NULL")

    # ---------------------------------------------------------------
    # 5. Poner la clave foranea. Solo tiene sentido despues del volcado.
    # ---------------------------------------------------------------
    op.create_foreign_key(
        "fk_limone_categoria_id",
        "limone",
        "categorias",
        ["categoria_id"],
        ["id"],
    )
```

Y reemplaza `downgrade()`:

```python
def downgrade() -> None:
    """Downgrade schema."""
    # Al reves: primero se suelta la columna, luego la tabla nueva.
    op.drop_constraint("fk_limone_categoria_id", "limone", type_="foreignkey")
    op.drop_column("limone", "categoria_id")
    op.drop_table("categorias")
    # NOTA: esto no restaura la columna "category" ni el Enum. Para eso
    # habria que volver a la migracion anterior. Ver B.9.
```

### El orden no se toca

El orden de los cinco pasos es lo que hace que funcione:

```
crear tabla  →  añadir columna (nullable)  →  volcar datos
            →  poner NOT NULL  →  poner la FK
```

Si pones la FK antes de volcar, PostgreSQL la rechaza porque hay filas sin
`categoria_id`. Si pones `NOT NULL` antes de volcar, rechaza las filas nulas.
**Ese es el 90% de los errores de esta parte.**

---

## B.5 Paso 4 — Quita la columna vieja y el Enum

Una vez aplicada y verificada la anterior, añade **otra migración** (no la
mezcles: así puedes deshacer cada cosa por separado).

```powershell
docker compose exec app alembic revision -m "quitar columna category y el enum"
```

```python
def upgrade() -> None:
    """Upgrade schema."""
    # El orden importa: primero se va la columna que usa el tipo,
    # y solo despues se puede borrar el tipo.
    #
    # ATENCION: Alembic NO tiene op.drop_type() ni op.create_type().
    # Compruebalo: las operaciones que existen son create_table,
    # drop_table, add_column, drop_column, alter_column, create_index,
    # create_foreign_key, rename_table, execute... y poco mas.
    # Para tocar un tipo Enum se hace SQL a mano con op.execute().
    op.drop_column("limone", "category")
    op.execute("DROP TYPE lemonadecategories")


def downgrade() -> None:
    """Downgrade schema."""
    # Reponer el Enum y la columna es SQL + rellenar desde categoria_id.
    # No se escribe "por si acaso": se escribe el dia que lo necesites,
    # con backup en la mano (seccion A.6.1).
    raise NotImplementedError(
        "Downgrade no implementado. Mira la seccion A.6.1."
    )
```

> El `downgrade()` lanza error **a propósito**, igual que en la Parte A.
> Restaurar la columna `category` exige recrear el tipo con `CREATE TYPE`,
> meter la columna otra vez como `nullable`, rellenarla desde `categoria_id`
> y solo después poner `NOT NULL` y quitar la clave foránea. Es código que se
> escribe el día que lo necesites, no antes.

> 💡 **Regla para recordar:** en Alembic solo existen operaciones sobre
> **tablas, columnas, índices y constraints**. Para todo lo que sea *tipo*
> (enums, dominios), es `op.execute("SQL a mano")`.

**Antes de aplicar, comprueba que nadie más usa el tipo:**

```powershell
docker compose exec postgres psql -U limone_user -d limone_db -c "SELECT table_name, column_name FROM information_schema.columns WHERE udt_name = 'lemonadecategories';"
```

Si devuelve filas, hay otra columna dependiendo del Enum: **no lo borres**.

---

## B.6 Paso 5 — Aplica y verifica

```powershell
docker compose exec app alembic upgrade head
docker compose exec app alembic current
docker compose exec app alembic history
```

Comprueba el resultado:

```powershell
docker compose exec postgres psql -U limone_user -d limone_db -c "SELECT p.id, p.name, p.price, c.nombre AS categoria FROM limone p JOIN categorias c ON c.id = p.categoria_id;"
```

Y en la API, prueba:

- `POST /lemonades` con `"categoria_id": 1` → `201`
- `GET /lemonades` → en el JSON ya no aparece `category`, aparece
  `categoria_id` con el número de la categoría

> **Ojo, esto es esperado.** El `GET /lemonades` no tiene ningún filtro por
> categoría hoy (`def get_lemonades(session: SessionDep)` no recibe nada más),
> así que ahí no se rompe nada. Lo que sí se rompe es el `POST` y el `PUT`,
> y lo verás en el error 5 de más abajo.

---

## B.7 Qué NO cambiar todavía

La tentación de cambiarlo todo a la vez es lo que rompe proyectos. Deja para
después, cada uno en su propia migración:

- [ ] Renombrar tabla `limone` → `productos`
- [ ] Renombrar la clase `Limone` → `Producto`
- [ ] Renombrar los campos a español (`name` → `nombre`)
- [ ] Cambiar `flavor` a opcional (para pasteles, que no tienen sabor)
- [ ] Borrar la clase `LemonadeCategories` del modelo
- [ ] Reescribir el filtro por categoría en el endpoint `GET /lemonades`

Cada uno es un cambio de código + una migración. **Uno por migración**, para
que cuando falle sepas exactamente cuál fue.

---

## B.8 Errores reales de la Parte B

### 1. `column "categoria_id" contains null values`

**La causa número 1.** Añadiste la columna como `NOT NULL` sobre una tabla
que ya tiene filas.

**Solución:** añádela primero `nullable=True`, haz el `UPDATE` de volcado, y
**después** `SET NOT NULL` (secciones B.4, pasos 2 → 4). Si ya la creaste mal
y no has llegado a aplicar nada, corrige el archivo y vuelve a correr. Si ya
se aplicó, haz `docker compose exec app alembic downgrade -1` y otra vez
`upgrade head`.

### 2. `insert or update on table "limone" violates foreign key constraint`

**Causa:** intentaste rellenar `categoria_id` con valores que no existen en
`categorias`, o la clave foránea se puso antes del volcado.

**Solución:** comprueba el orden. La tabla `categorias` y sus filas tienen
que existir **antes** de tocar `categoria_id`.

### 3. `column "categoria_id" contains null values` en `SET NOT NULL`

**Causa:** el `UPDATE` no cubrió todas las filas. Normalmente pasa porque
hay un valor en la columna `category` que no estaba en el Enum.

**Diagnóstico:**

```powershell
docker compose exec postgres psql -U limone_user -d limone_db -c "SELECT DISTINCT category::text, COUNT(*) FROM limone GROUP BY 1;"
```
```powershell
docker compose exec postgres psql -U limone_user -d limone_db -c "SELECT unnest(enum_range(NULL::lemonadecategories));"
```

Si aparece un valor en la primera consulta que no está en la segunda, esa
fila no tiene dónde casar. Añade la categoría que falta y repite.

### 4. `relation "limone" does not exist`

**Causa:** renombraste la tabla en el modelo (`__tablename__ = "productos"`)
y Alembic generó `drop_table` + `create_table`.

**Solución:** **no aplicada nunca.** Revisa el archivo de migración antes de
`upgrade head`. Si ya la aplicaste y tenías datos, es cuando necesitas el
`backup_antes_de_deshacer.sql` de la sección A.6.1. Por eso la regla es:
**leer el archivo de migración siempre, antes de aplicarlo.**

### 5. `AttributeError: 'LimoneCreate' object has no attribute 'category'`

**Causa:** cambiaste el modelo, pero **`main.py` todavía escribe en la
columna vieja**. Hay dos sitios concretos:

- `main.py:105` → `category=data.category,` (dentro del `POST`)
- `main.py:146` → `limone.category = data.category` (dentro del `PUT`)

Como `LimoneCreate` ya no tiene `category`, Python revienta en cuanto llega
una petición.

**Solución:** en los dos sitios, cambia `category` por `categoria_id`:

```python
# ANTES (POST, main.py:105)
category=data.category,

# DESPUES
categoria_id=data.categoria_id,
```

```python
# ANTES (PUT, main.py:146)
limone.category = data.category

# DESPUES
limone.categoria_id = data.categoria_id
```

**Esto es código, no migración.** Si la app no arranca y en la terminal ves
`UndefinedColumn` en vez de esto, significa que el modelo ya cambió pero la
base de datos no: te falta `docker compose exec app alembic upgrade head`.
Son dos problemas distintos: **`AttributeError` = falta código;
`UndefinedColumn` = falta migración.**

> El `GET /lemonades` no tiene filtro por categoría, así que ahí no hay nada
> que arreglar. Si algún día añades un filtro, ten en cuenta que ya no se
> puede buscar en una columna `category` que no existe: haría falta un `JOIN`
> con `categorias`.

### 6. `Multiple head revisions are present`

Mismo caso que en A.8.3: dos migraciones con el mismo `down_revision`.

```powershell
docker compose exec app alembic heads
docker compose exec app alembic history
```

Borra el archivo que no quieras de `alembic/versions/`.

---

## B.9 Checklist de la Parte B

### Modelo
- [ ] Creé `class Categoria` con `__tablename__ = "categorias"`
- [ ] Cambié `category` por `categoria_id` con `foreign_key`
- [ ] **No** renombré nada más todavía

### Migración 1 (crear estructura + volcar datos)
- [ ] Vi `create_table('categorias')` en el archivo generado
- [ ] Vi `add_column('limone', 'categoria_id')`
- [ ] **No** vi `drop_table('limone')` → si lo vi, no aplico
- [ ] La columna entra como `nullable=True`, no `NOT NULL`
- [ ] Escribí a mano el `INSERT` de categorías
- [ ] Escribí a mano el `UPDATE` de volcado
- [ ] `SET NOT NULL` viene **después** del volcado
- [ ] La clave foránea va la **última**

### Migración 2 (limpiar)
- [ ] `drop_column` de `category` **antes** del `DROP TYPE`
- [ ] Comprobé con `information_schema.columns` que nadie más usa el tipo

### Aplicación
- [ ] `alembic upgrade head` sin errores
- [ ] `alembic current` muestra `(head)`
- [ ] El `JOIN categorias` devuelve datos
- [ ] El `POST` con `categoria_id` devuelve `201`

---
---

## Resumen: ¿A o B?

| Pregunta | Respuesta |
|---|---|
| ¿Solo añado una categoría de vez en cuando? | **A** — Enum + migración |
| ¿Va a crecer la lista (agua, pasabocas, pasteles)? | **B** — tabla `categorias` |
| ¿Quiero que alguien añada categorías sin tocar código? | **B** |
| ¿Los campos de cada producto son muy distintos? | Ni A ni B: tablas por tipo |

---

## Siguientes pasos para tu catálogo

Cuando quieras meter agua, pasabocas y pasteles de verdad, el orden que
recomiendo es:

1. **Termina esto primero.** Que la migración a tabla `categorias` esté
   aplicada, verificada y con backup.
2. **Decide el modelo en papel** antes de escribir código: ¿un `sabor` que
   solo aplica a bebidas? ¿un `peso` que solo aplica a pasteles? ¿fecha de
   caducidad? Hazte esas preguntas **antes** de tocar `main.py`.
3. **Camino fácil:** una sola tabla con los campos comunes
   (`name`, `price`, `categoria_id`) y los campos especiales como opcionales.
   Solo crea tablas separadas cuando te sobre un campo que no significa nada
   para la mitad de tus productos.
4. **Una migración por cambio.** Nunca metas dos ideas en el mismo archivo.

Y recuerda: todo esto te lo permite el trabajo de la guía 2. Cada vez que
cambies la estructura vas a agradecer tener Alembic.

---

## Y ahora qué

- ¿Quieres entender mejor los Enums y el resto del vocabulario? → `00-conceptos.md`
- ¿Prefieres que alguien te lleve de la mano con todo el CRUD? → `01-guia-crud-fastapi.md`
- ¿Problemas con Docker, migraciones o PostgreSQL? → `02-guia-docker-postgres.md`, sección 10
