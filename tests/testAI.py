import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from src.AICorrector import AICorrection, MODELS_DIR, load_model

load_model(MODELS_DIR / "qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf")

auto = """
# ChangeLog__report0000__vs__report0004

## Units

### ADDED+
- U0009 Intensity

### MODIFIED
- U0004 Edge Pitch
  - added params:
    - FLTR[0].BLDG
    - FLTR[0].PRD
    - FLTR[0].PTMS
  - modified params:
    - FLTR[0].FTYP
      - value: "0" -> "26"

## Variables

### ADDED+
- '#PitchNumber'

## Logic blocks (`unit_*.txt`)


### MODIFIED
- U0006 Calculation
  - line differences:
    - insert: new lines `2-3` added
      - NEW:
        - `#PitchNumber = !U[0004].RSLT.N:MS`
        - `'Commento aggiunto`

## Comments:


Qualsiasi testi che non rispetti il formato richiesto è un errore.
"""
human = "aggiunta u9, modif.u4 e u6"

result = AICorrection(auto, human)

print(result)
