from pathlib import Path
from llama_cpp import Llama
import sys

from src.modelSelector import detect_hardware

# src/AICorrector.py -> risalgo alla root del progetto
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

MODELS_DIR = BASE_DIR / "models"
PROMPT = (BASE_DIR / "src" / "promptCorrettore.txt").read_text(encoding="utf-8")

llm = None
_current_model_path = None


def get_current_model_path():
    return _current_model_path


def load_model(model_path):
    """Carica (o ricarica) il modello GGUF indicato come modulo llm
    attivo, scegliendo i parametri GPU/CPU in base all'hardware rilevato
    a runtime (sostituisce il vecchio flag manuale GPU_Nvidia)."""
    global llm, _current_model_path

    model_path = str(model_path)
    hardware = detect_hardware()
    use_gpu = bool(hardware.get("vram_gb"))

    if llm is not None:
        llm.close()
        llm = None

    if use_gpu:
        llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=hardware.get("cpu_cores") or 8,
            n_gpu_layers=-1,
            n_batch=512,
            verbose=True
        )
    else:
        llm = Llama(
            model_path=model_path,
            n_ctx=32768,
            n_threads=hardware.get("cpu_cores") or 8,
            verbose=False
        )

    _current_model_path = model_path
    return _current_model_path


def AICorrection(auto, human):
    if llm is None:
        raise RuntimeError("Nessun modello AI caricato.")

    risposta = llm.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": PROMPT
            },
            {
                "role": "user",
                "content": "//AUTO\n" + auto + "\n//HUMAN\n" + human
            }
        ],
        temperature=0.0,
        top_p=0.6,
        repeat_penalty=1.15,
        max_tokens=100000

    )
    risposta = str(risposta["choices"][0]["message"]["content"])

    if "</think>" in risposta: # Togli la sezione thinking dalla risposta
        risposta = risposta.split("</think>", 1)[1].strip()

    return risposta
