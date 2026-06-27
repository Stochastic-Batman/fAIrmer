from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from lang2lang import create_models, translate
from pydantic import BaseModel


_models: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    (tok_ka_en, mdl_ka_en), (tok_en_ka, mdl_en_ka) = create_models("ka", "en")
    _models["ka->en"] = (tok_ka_en, mdl_ka_en)
    _models["en->ka"] = (tok_en_ka, mdl_en_ka)
    yield
    _models.clear()


app = FastAPI(lifespan=lifespan)


class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str


@app.post("/translate")
def translate_text(req: TranslateRequest):
    key = f"{req.source_lang}->{req.target_lang}"
    pair = _models.get(key)
    if pair is None:
        raise HTTPException(status_code=400, detail=f"Unsupported language pair: {key}")
    tokenizer, model = pair
    return {"translated_text": translate(req.text, tokenizer, model)}
