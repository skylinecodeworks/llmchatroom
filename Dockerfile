FROM python:3.12-slim

# Instala curl, instala uv en ~/.local/bin y lo vincula a /usr/local/bin
RUN apt-get update && apt-get install -y curl && \
    curl -Ls https://astral.sh/uv/install.sh | bash && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv && \
    apt-get purge -y curl && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*


# Asegurar el PATH
ENV PATH="/root/.local/bin:/usr/local/bin:$PATH"

WORKDIR /app

# Instala dependencias con uv
COPY pyproject.toml .
COPY uv.lock .
RUN uv pip install --system --no-deps .

# Copia el resto de la app
COPY . .

CMD ["uv", "run", "main.py"]
