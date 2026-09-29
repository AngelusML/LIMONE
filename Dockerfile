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
