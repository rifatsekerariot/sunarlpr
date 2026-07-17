FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download PaddleOCR models (English & Turkish/Latin) into the image using curl & tar to avoid Python segmentation faults in buildx
RUN apt-get update && apt-get install -y --no-install-recommends curl tar && \
    mkdir -p /root/.paddleocr/whl/det/en/en_PP-OCRv3_det_infer \
             /root/.paddleocr/whl/det/multilingual/Multilingual_PP-OCRv3_det_infer \
             /root/.paddleocr/whl/rec/en/en_PP-OCRv4_rec_infer \
             /root/.paddleocr/whl/rec/latin/latin_PP-OCRv3_rec_infer \
             /root/.paddleocr/whl/cls/ch_ppocr_mobile_v2.0_cls_infer && \
    curl -sSL https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_det_infer.tar | tar -xC /root/.paddleocr/whl/det/en/en_PP-OCRv3_det_infer --strip-components=1 && \
    curl -sSL https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/Multilingual_PP-OCRv3_det_infer.tar | tar -xC /root/.paddleocr/whl/det/multilingual/Multilingual_PP-OCRv3_det_infer --strip-components=1 && \
    curl -sSL https://paddleocr.bj.bcebos.com/PP-OCRv4/english/en_PP-OCRv4_rec_infer.tar | tar -xC /root/.paddleocr/whl/rec/en/en_PP-OCRv4_rec_infer --strip-components=1 && \
    curl -sSL https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/latin_PP-OCRv3_rec_infer.tar | tar -xC /root/.paddleocr/whl/rec/latin/latin_PP-OCRv3_rec_infer --strip-components=1 && \
    curl -sSL https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar | tar -xC /root/.paddleocr/whl/cls/ch_ppocr_mobile_v2.0_cls_infer --strip-components=1 && \
    apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*




COPY . .

CMD ["python", "main.py"]
