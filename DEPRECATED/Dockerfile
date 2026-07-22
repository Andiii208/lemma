FROM python:3.12-slim AS backend

WORKDIR /app

# 安装系统依赖（LaTeX、字体、通用工具）
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-xetex \
    texlive-lang-chinese \
    texlive-latex-extra \
    fonts-noto-cjk \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制后端依赖文件
COPY backend/pyproject.toml /app/backend/pyproject.toml

# 安装 Python 依赖
RUN pip install --no-cache-dir \
    fastapi>=0.111.0 \
    uvicorn[standard]>=0.30.0 \
    websockets>=12.0 \
    openai>=1.30.0 \
    pydantic>=2.0.0 \
    chromadb>=0.5.0 \
    tiktoken>=0.7.0 \
    pyyaml>=6.0 \
    httpx>=0.27.0 \
    jinja2>=3.1.0 \
    python-multipart>=0.0.9 \
    aiofiles>=23.0 \
    matplotlib>=3.8.0 \
    numpy>=1.26.0 \
    scipy>=1.12.0

# 复制后端代码和领域配置
COPY backend/ /app/backend/
COPY domains/ /app/domains/

# 设置 Python 路径
ENV PYTHONPATH=/app/backend/src

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8765/api/health || exit 1

CMD ["python", "-m", "uvicorn", "lemma.api.server:app", "--host", "0.0.0.0", "--port", "8765"]
