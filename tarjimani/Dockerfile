FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Download both translation models into the image at build time so the container starts instantly instead of pulling ~1.5 GB on every cold start.
RUN python -c "from lang2lang import create_models; create_models('ka', 'en')"

EXPOSE 5000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5000"]
