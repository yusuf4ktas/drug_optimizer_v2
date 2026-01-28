FROM python:3.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY --chown=user ./requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code
COPY --chown=user . .

# Pre-download the BERT model during build
RUN python -c "from transformers import pipeline; pipeline('ner', model='d4data/biomedical-ner-all', aggregation_strategy='none')"

# 7. Expose the port Hugging Face expects (7860)
EXPOSE 7860

# 8. Run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]