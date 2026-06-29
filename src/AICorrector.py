from pathlib import Path
from llama_cpp import Llama
import sys

PROMPT = open("src/promptCorrettore.txt", "r", encoding="utf-8").read()

# src/AICorrector.py -> risalgo alla root del progetto

# BASE_DIR = Path(__file__).resolve().parent.parent

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

#MODEL_PATH = BASE_DIR / "models" / "Qwen3-1.7B-Q4_K_M.gguf"
MODEL_PATH = BASE_DIR / "models" / "qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Modello non trovato: {MODEL_PATH}")

GPU_Nvidia = True
llm = None
if GPU_Nvidia:
    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=4096,
        n_threads=8,
        n_gpu_layers=-1,
        n_batch=512,
        verbose=True
    )
else:
    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=32768,
        n_threads=8,
        verbose=False
    )

def AICorrection(auto, human):
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