FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y \
        wget \
        unzip \
        libglib2.0-0 \
        libnss3 \
        libgconf-2-4 \
        libfontconfig1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcairo2 \
        libcups2 \
        libcurl3-gnutls \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libpango-1.0-0 \
        libu2f-udev \
        libvulkan1 \
        libx11-6 \
        libxcb1 \
        fonts-liberation \
        xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb \
    && apt-get install -y ./google-chrome-stable_114.0.5735.90-1_amd64.deb \
    && rm google-chrome-stable_114.0.5735.90-1_amd64.deb

RUN wget -q https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chromedriver --version

COPY ./app/requirements.txt .

RUN pip install -r requirements.txt

COPY ./app .

CMD ["python", "main.py"]
