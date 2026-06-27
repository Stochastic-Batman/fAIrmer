# fAIrmer: ML-Powered Agricultural Assistant for Farmers

`fAIrmer` is an agricultural advisory platform that puts expert agronomic knowledge directly in the hands of farmers. In many rural communities, particularly in Georgia, smallholder farmers lack access to professional agronomists and rely on neighbors for advice - which is often unverified or outdated. `fAIrmer` addresses this by combining a fine-tuned vision model for spoilage detection with a reasoning LLM for crop consultation, all delivered in Georgian through an automated translation pipeline.

Farmers connect to the web interface, submit questions in Georgian, and upload crop images - the system handles translation, inference, and localization with no external API dependencies.

## Technologies

- **Frontend:** Svelte 5, SvelteKit, `adapter-node` (for self-containedness)
- **Backend:** FastAPI, SQLite
- **Vision Model:** EfficientNet-B0 fine-tuned on [Food Freshness Dataset](https://www.kaggle.com/datasets/ulnnproject/food-freshness-dataset) (13 produce categories, binary freshness classification) - model named კოი (Koi)
- **LLM:** DeepSeek-R1-Distill-Qwen-7B via Ollama, prompted to replicate [persadian/CropSeek-LLM](https://huggingface.co/persadian/CropSeek-LLM) agricultural domain behavior - served as ბარბალე (Barbale)
- **Translation:** [Helsinki-NLP/opus-mt-ka-en](https://huggingface.co/Helsinki-NLP/opus-mt-ka-en) and [Helsinki-NLP/opus-mt-synthetic-en-ka](https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-ka) (bidirectional Georgian <-> English) via MarianMT
- **Infrastructure:** Docker, Docker Compose

## Setup

### Prerequisites

- Docker with Compose v2 (verify via `docker compose version`)
- ~8 GB free disk space (translation models + LLM weights)

### Run

Clone the repo:
```bash
git clone https://github.com/Stochastic-Batman/fAIrmer.git && cd fAIrmer
```

The command below may take ~30 minutes:
```bash
docker compose up --build
```

On first run, the `tarjimani` image build downloads the Helsinki-NLP translation models (~1.5 GB) and the `ollama` container pulls `deepseek-r1:7b` (~4.7 GB). Both are cached in Docker volumes and only downloaded once.

Once all services are up, open `http://localhost:3000`.

### First use

1. Sign up with a username and password (optionally add region, primary crop, and soil metrics)
2. Ask a crop question in Georgian in the "ბარბალე" chat panel
3. Upload a crop image in the scanner panel to check freshness - if rotten, a Georgian mitigation advisory is generated automatically

## Project Structure

```
fAIrmer/
├── backend/
│   ├── Dockerfile
│   ├── database.py         # SQLite connection and schema init
│   ├── main.py             # FastAPI endpoints and pipeline orchestration
│   ├── models.py           # CRUD functions for users, chat, alerts
│   ├── models/
│   │   └── koi.pt          # Fine-tuned EfficientNet-B0 weights
│   ├── requirements.txt
│   └── vision_engine.py    # Koi model loader and inference
├── data/                   # Persistent SQLite volume mount
├── docker-compose.yaml
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── app.html
│   │   └── routes/
│   │       ├── +layout.svelte      # Global styles and favicon
│   │       ├── +page.svelte        # Gateway Portal (login / sign up)
│   │       └── barbale/
│   │           └── +page.svelte    # Barbale workspace (chat + scanner)
│   ├── static/
│   │   └── fAIrmer.png
│   └── vite.config.ts
├── notebooks/
│   └── Koi.ipynb           # Colab training notebook for the vision model
└── tarjimani/
    ├── Dockerfile
    ├── lang2lang.py        # MarianMT model loader
    ├── requirements.txt
    └── server.py           # Translation HTTP service (POST /translate)
```
