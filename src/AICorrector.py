from ollama import chat

PROMPT = """
Sei un correttore professionale.

NON ripetere mai il prompt ricevuto.
NON riportare il testo di AUTO.
NON riportare il testo di HUMAN.
Restituisci esclusivamente il risultato finale.

- Lingua:  italiano o inglese, rispondi nella lingua in cui vieni interpellato

- Ti verranno sottoposti testi che descrivono le modifiche tra due versioni di software Keyence divisi in due parti: contraddistinte da //AUTO e //HUMAN
- //AUTO è una sezione schematica generata automaticamente che indica quali blocchi sono stati modificati
- //HUMAN è la sezione scritta dall'operatore che descrive in maniera spesso inprecisa e sgrammaticata le modifiche

- La tua risposta si divide in Correzione e Suggerimento secondo questo formato:

//Correzione:
In questa sezione restituisci solo il testo //HUMAN corretto secondo i criteri sotto:
- Correggi grammatica e ortografia.
- Mantieni il significato non aggiungere nulla in questa sezione
- Quando viene citata una unit sostituisci con riformattazione come esempio nel blocco human: (//AUTO U0006 Calculation, //HUMAN u6, -> //Correzione: U0006 Calculation)

//Suggerimento:
In questa sezione restituisci solo domande secondo le linee guida sotto:
- Quando una modifica contenuta in AUTO non viene menzionata in HUMAN suggerisci che venga commentata
- Proponi i suggerimenti che ti sembra più importanti, non più di 3.
"""

def AICorrection(auto, human):

    risposta = chat(
        model="qwen3:1.7b",
        messages=[
            {
                "role": "system",
                "content": PROMPT
            },
            {
                "role": "user",
                "content": "//AUTO\n" + auto + "\n//HUMAN\n" + human
            }
        ]
    )

    return risposta["message"]["content"]

auto = """
# ChangeLog__report0000__vs__report0004

## Units

### ADDED+
- `U0009`

### MODIFIED
- `U0004`
  - added params:
    - `FLTR[0].BLDG`
    - `FLTR[0].PRD`
    - `FLTR[0].PTMS`
  - modified params:
    - `FLTR[0].FTYP`
      - value: "0" -> "26"

## Variables

### ADDED+
- `#PitchNumber`

## Logic blocks (`unit_*.txt`)


### MODIFIED
- `MTX0006`
  - old file: `unit_0000_20260622_102302_MTX0006.txt`
  - new file: `unit_0000_20260624_095816_MTX0006.txt`
  - line differences:
    - insert: new lines `2-3` added
      - NEW:
        - `#PitchNumber = !U[0004].RSLT.N:MS`
        - `'Commento aggiunto`

## Comments:
"""

human = "cambiata U4 con filtro gauss, modificato blocco logico 6"

# print(
#     AICorrection(
#         auto, human
#     )
# )