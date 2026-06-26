import sys
from pathlib import Path
from llama_cpp import Llama

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from src.AICorrector import AICorrection

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
Added U0009 Modified U0004 Edge Pitch: added Gaussian filter modified U0006


Qualsiasi testi che non rispetti il formato richiesto è un errore.
"""
human = "aggiunta u9, modif.u4 e u6"

result = AICorrection(auto, human)

print(result)


# llm = Llama(
#     model_path="models/Qwen3-1.7B-Q4_K_M.gguf",
#     chat_format="chatml",
#     n_ctx=8192,
#     verbose=False
# )

# r = llm.create_completion(   
#     prompt="scrivi solo: ciao!",
#     temperature=0,
#     top_p=0.5,
#     repeat_penalty=1.15,
#     max_tokens=200

# )

# print(r)
