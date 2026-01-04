FROM python:3.11-slim

# Install system deps for Playwright
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates curl \
    libx11-xcb1 libxrandr2 libxcomposite1 libxcursor1 libxdamage1 libxfixes3 libxi6 \
    libgtk-3-0 libatk1.0-0 libcairo2 libcairo-gobject2 libgdk-pixbuf2.0-0 libasound2 \
    libpangocairo-1.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN python -m playwright install --with-deps && python -m playwright install

# Copy application
COPY . /app

EXPOSE 8501

ENV PYTHONUNBUFFERED=1

CMD ["bash", "-lc", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
