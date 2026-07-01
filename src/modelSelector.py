"""
Rilevamento hardware e selezione automatica del modello AI (GGUF) fra
quelli disponibili in models/, in base alle risorse della macchina in uso.
"""
import ctypes
import os
import re
import subprocess

MODEL_CATALOG = [
    {
        "match": "Qwen3-1.7B-Q4_K_M.gguf",
        "display_name": "Qwen3 1.7B (leggero, CPU)",
        "tier": "light",
        "min_ram_gb": 8,
        "min_vram_gb": None,
    },
    {
        "match": "Qwen2.5-3B-Instruct-Q4_K_M.gguf",
        "display_name": "Qwen2.5 3B (medio, CPU/GPU)",
        "tier": "medium",
        "min_ram_gb": 16,
        "min_vram_gb": 3,
    },
    {
        "match": "qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf",
        "display_name": "Qwen2.5 7B (potente, GPU consigliata)",
        "tier": "heavy",
        "min_ram_gb": 16,
        "min_vram_gb": 6,
    },
    {
        "match": "qwen2.5-3b-instruct-fp16-00001-of-00002.gguf",
        "display_name": "Qwen2.5 3B (medio, GPU consigliata)",
        "tier": "heavy",
        "min_ram_gb": 16,
        "min_vram_gb": 6,
    },
]

_SHARD_RE = re.compile(r"^(?P<base>.+)-(?P<part>\d{5})-of-(?P<total>\d{5})\.gguf$", re.IGNORECASE)


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _get_total_ram_gb():
    try:
        stat = _MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return stat.ullTotalPhys / (1024 ** 3)
    except (AttributeError, OSError):
        return None


def _get_nvidia_gpu():
    try:
        mem_out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if mem_out.returncode != 0 or not mem_out.stdout.strip():
            return None, None

        vram_mb = float(mem_out.stdout.strip().splitlines()[0].strip())

        name_out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        gpu_name = name_out.stdout.strip().splitlines()[0] if name_out.returncode == 0 and name_out.stdout.strip() else "NVIDIA GPU"

        return gpu_name, vram_mb / 1024
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None, None


def detect_hardware():
    """Ritorna le caratteristiche hardware rilevanti per la scelta del
    modello: numero di core CPU, RAM totale (GB) e, se presente, nome/VRAM
    (GB) di una GPU NVIDIA. I valori non rilevabili sono None."""
    gpu_name, vram_gb = _get_nvidia_gpu()
    return {
        "cpu_cores": os.cpu_count() or 4,
        "ram_gb": _get_total_ram_gb(),
        "gpu_name": gpu_name,
        "vram_gb": vram_gb,
    }


def _find_catalog_entry(filename):
    for entry in MODEL_CATALOG:
        if entry["match"].lower() == filename.lower():
            return entry
    return None


def _group_shards(models_dir):
    """Raggruppa i file .gguf di models_dir per modello: i file singoli
    formano un gruppo da soli, quelli split (xxx-00001-of-0000N.gguf)
    vengono raggruppati per nome base e accettati solo se TUTTI gli shard
    attesi sono presenti."""
    if not os.path.isdir(models_dir):
        return []

    files = [f for f in os.listdir(models_dir) if f.lower().endswith(".gguf")]
    groups = {}
    for f in files:
        m = _SHARD_RE.match(f)
        if m:
            key = (m.group("base"), int(m.group("total")))
        else:
            key = (f, 1)
        groups.setdefault(key, []).append(f)

    result = []
    for (_base, total), shard_files in groups.items():
        if len(shard_files) < total:
            continue
        shard_files_sorted = sorted(shard_files)
        entry_file = shard_files_sorted[0]
        result.append({
            "entry_filename": entry_file,
            "size_bytes": sum(os.path.getsize(os.path.join(models_dir, f)) for f in shard_files),
        })
    return result


def list_available_models(models_dir):
    """Elenca i modelli completi (tutti gli shard presenti) trovati in
    models_dir. Ogni voce include path/nome, dimensione totale in byte e,
    se il file è in MODEL_CATALOG, nome descrittivo e tier; altrimenti
    viene comunque elencato con il proprio filename come display_name."""
    models = []
    for shard_group in _group_shards(models_dir):
        filename = shard_group["entry_filename"]
        catalog_entry = _find_catalog_entry(filename)
        models.append({
            "path": os.path.join(models_dir, filename),
            "filename": filename,
            "display_name": catalog_entry["display_name"] if catalog_entry else filename,
            "tier": catalog_entry["tier"] if catalog_entry else "unknown",
            "min_ram_gb": catalog_entry["min_ram_gb"] if catalog_entry else None,
            "min_vram_gb": catalog_entry["min_vram_gb"] if catalog_entry else None,
            "size_bytes": shard_group["size_bytes"],
        })

    return sorted(models, key=lambda m: m["filename"].lower())


def recommend_model(available_models, hardware):
    """Sceglie il modello più adatto fra quelli disponibili in base
    all'hardware rilevato: GPU NVIDIA con VRAM sufficiente -> tier 'heavy';
    altrimenti RAM sufficiente -> tier 'medium'; altrimenti -> tier
    'light'. Se il tier preferito non è disponibile si scende di livello;
    se nessun modello noto è disponibile si ritorna comunque il più
    piccolo fra quelli trovati, per garantire sempre un default."""
    if not available_models:
        return None

    by_tier = {}
    for m in available_models:
        by_tier.setdefault(m["tier"], []).append(m)

    ram_gb = hardware.get("ram_gb") or 0
    vram_gb = hardware.get("vram_gb") or 0

    if vram_gb >= 6 and by_tier.get("heavy"):
        preferred = "heavy"
    elif (vram_gb >= 3 or ram_gb >= 16) and by_tier.get("medium"):
        preferred = "medium"
    elif by_tier.get("light"):
        preferred = "light"
    elif by_tier.get("medium"):
        preferred = "medium"
    elif by_tier.get("heavy"):
        preferred = "heavy"
    else:
        preferred = None

    if preferred:
        return min(by_tier[preferred], key=lambda m: m["size_bytes"])

    return min(available_models, key=lambda m: m["size_bytes"])
