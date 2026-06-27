import io
import os
import torch
import torch.nn as nn
import torchvision.models as tv_models
import torchvision.transforms as T
from PIL import Image


MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "koi.pt")


# 13 classes from the Food Freshness Dataset (https://www.kaggle.com/datasets/ulnnproject/food-freshness-dataset).
# If I had trained Koi locally, I would have made this dynamic (extract subfolder names), but since I trained this on Colab and I do not have the dataset locally anymore, I simply hardcoded this list.
# I believe this is okay for the hackathon demo.
PRODUCE_CLASSES = ["Apple", "Banana", "Bell Pepper", "Bitter Gourd", "Capsicum", "Carrot", "Cucumber", "Mango", "Okra", "Orange", "Potato", "Strawberry", "Tomato"]
FRESHNESS_CLASSES = ["Fresh", "Rotten"]


# official standard for evaluating images on EfficientNet-B0 in PyTorch
_transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class Koi(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = tv_models.efficientnet_b0(weights=None)
        self.backbone.classifier = nn.Identity()
        self.head_produce = nn.Sequential(nn.Dropout(p=0.2, inplace=False), nn.Linear(1280, 13))
        self.head_state = nn.Sequential(nn.Dropout(p=0.2, inplace=False), nn.Linear(1280, 2))

    def forward(self, x):
        features = self.backbone(x)
        return self.head_produce(features), self.head_state(features)


def _load_model() -> Koi:
    model = Koi()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=True))
    model.eval()
    return model


_model: Koi | None = None


def get_model() -> Koi:
    global _model
    if _model is None:
        _model = _load_model()
    return _model


def classify(image_bytes: bytes) -> dict:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(image).unsqueeze(0)

    with torch.no_grad():
        logits_produce, logits_state = get_model()(tensor)

    produce_idx = logits_produce.argmax(dim=1).item()
    state_probs = torch.softmax(logits_state, dim=1)[0]
    state_idx = state_probs.argmax().item()

    return {
        "produce": PRODUCE_CLASSES[produce_idx],
        "freshness": FRESHNESS_CLASSES[state_idx],
        "confidence": round(state_probs[state_idx].item(), 4),
    }
