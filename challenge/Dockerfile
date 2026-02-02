FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PostgreSQL and ffmpeg (needed for Whisper)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy project
COPY . .

# Create directory for temporary files
RUN mkdir -p /app/temp_audio

EXPOSE 8000

# Command to run the application
# As we are in a testing environment, we dont need to use a production server like gunicorn
CMD ["sh", "-c", "uv run python manage.py migrate && uv run python manage.py runserver 0.0.0.0:8000"]