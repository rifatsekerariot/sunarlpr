FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download PaddleOCR PP-OCRv4 models into the image
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='en', ocr_version='PP-OCRv4', use_space_char=False)"

COPY . .

CMD ["python", "main.py"]
