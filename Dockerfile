FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

RUN uv sync --frozen --no-dev

# EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "dashboard.py", "--server.address=0.0.0.0"]
