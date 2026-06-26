from pathlib import Path
from llama_cpp import Llama

PROMPT = """
Sei un correttore tecnico Keyence.

Rispondi esclusivamente nel formato seguente.

//Correzione:
<testo corretto>

//Suggerimento:
<domande o "Nessun suggerimento">

Regole:

- Correggi grammatica e ortografia di HUMAN.
- Mantieni il significato.
- Non inventare informazioni.
- Non riportare AUTO.
- Non riportare HUMAN.
- Non fornire spiegazioni.
- Non mostrare ragionamenti.
- Non aggiungere testo fuori dalle due sezioni.
- Se una unità abbreviata è presente in AUTO, sostituiscila con il nome completo.
- Se AUTO contiene modifiche importanti non commentate in HUMAN, suggeriscile.
- Massimo 3 suggerimenti.

Qualsiasi testo fuori dal formato richiesto è un errore.

ESEMPIO

INPUT

//AUTO
ADDED+
- U0009 Intensity

MODIFIED
- U0004 Edge Pitch

Variables
ADDED+
- '#PitchNumber'

//HUMAN
modifica u6, aggiunta u9 edgep.

OUTPUT

//Correzione:
Modificata U0006 Calculation.
Aggiunta U0009 Edge Pitch.

//Suggerimento:
Commenta l'aggiunta della variabile '#PitchNumber'

"""

# src/AICorrector.py -> risalgo alla root del progetto
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "Qwen3-1.7B-Q4_K_M.gguf"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Modello non trovato: {MODEL_PATH}")

# Carica il modello una sola volta
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
        max_tokens=1200

    )
    risposta = str(risposta["choices"][0]["message"]["content"])   

    if "</think>" in risposta: # Togli la sezione thinking dalla risposta
        risposta = risposta.split("</think>", 1)[1].strip()

    return risposta