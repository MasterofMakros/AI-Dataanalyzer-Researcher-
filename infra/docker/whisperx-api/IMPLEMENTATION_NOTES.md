# WhisperX Implementation Notes
## Neural Vault / Conductor

**Last Updated**: 2026-01-10

---

## Problem History

### Issue 1: PyTorch `weights_only=True` Crash (v2.1.1 - v2.1.3)
**Error**:
```
_pickle.UnpicklingError: Weights only load failed.
Unsupported global: GLOBAL pyannote.audio.core.task.Resolution
```

**Root Cause**:
- PyTorch 2.6+ changed the default of `torch.load(weights_only=...)` from `False` to `True`
- Pyannote checkpoints contain serialized Python objects (OmegaConf, Resolution, etc.)
- These are blocked by the new security-focused default

**Attempted Fixes**:
1. ❌ Monkey patch `torch.load` to default `weights_only=False` - Did not work, internal calls bypass patch
2. ❌ Pin `torch==2.4.1` to avoid new default - Incompatible with newer pyannote versions
3. ⚠️ `torch.serialization.add_safe_globals()` - Correct approach but requires complete type list

### Issue 2: Version Incompatibility
**Discovery**: Official WhisperX v3.7.4 (as of 2026-01-10) requires:
- `torch~=2.8.0` (NOT 2.4.1)
- `torchaudio~=2.8.0`
- `pyannote-audio>=3.3.2,<4.0.0`
- `ctranslate2>=4.5.0` (cuDNN 9 support)

Our implementation was using:
- `torch==2.4.1` (outdated)
- `pyannote.audio>=3.1.0` (too old)

---

## Correct Implementation (v2.1.4+)

### Key Requirements (from WhisperX pyproject.toml):
```toml
dependencies = [
    "ctranslate2>=4.5.0",
    "faster-whisper>=1.1.1",
    "pyannote-audio>=3.3.2,<4.0.0",
    "torch~=2.8.0",
    "torchaudio~=2.8.0",
    "transformers>=4.48.0",
]
```

### Docker Build Strategy:
1. Use NVIDIA CUDA 12.8 base image (for PyTorch 2.8 compatibility)
2. Install WhisperX directly from PyPI or git (includes correct dependencies)
3. Let WhisperX manage its own transitive dependencies

### Safe Globals for Pyannote (if needed):
From WhisperX PR #1313:
```python
from omegaconf import DictConfig, ListConfig
from omegaconf.base import ContainerMetadata, Metadata
from omegaconf.nodes import AnyNode, BooleanNode, FloatNode, IntegerNode, StringNode
from pyannote.audio.core.model import Introspection
from pyannote.audio.core.task import Problem, Resolution, Specifications
from torch.torch_version import TorchVersion

torch.serialization.add_safe_globals([
    DictConfig, ListConfig, ContainerMetadata, Metadata,
    AnyNode, BooleanNode, FloatNode, IntegerNode, StringNode,
    TorchVersion, Introspection, Specifications, Problem, Resolution,
])
```

---

## HuggingFace Token für Speaker Diarization

WhisperX unterstützt **Speaker Diarization** (Sprecher-Erkennung), die automatisch erkennt, welcher Sprecher gerade spricht. Diese Funktion erfordert einen HuggingFace Token.

### Was ist Speaker Diarization?
- Erkennt automatisch verschiedene Sprecher in Audio/Video
- Kennzeichnet Segmente mit Sprecher-IDs (SPEAKER_00, SPEAKER_01, etc.)
- Ideal für Meetings, Interviews, Podcasts

### Token einrichten:
1. **Token erstellen**: https://huggingface.co/settings/tokens
   - Token-Typ: "Read" reicht aus
2. **Nutzungsbedingungen akzeptieren**: https://huggingface.co/pyannote/speaker-diarization-3.1
3. **Token in `.env` eintragen**: `HF_TOKEN=hf_xxxxx...`
4. **WhisperX neu starten**: `docker compose restart whisperx`

### Funktionen ohne/mit Token:
| Funktion | Ohne Token | Mit Token |
|----------|------------|-----------|
| Transkription | ✅ | ✅ |
| Word-Level Timestamps | ✅ | ✅ |
| Speaker Diarization | ❌ | ✅ |

- WhisperX GitHub: https://github.com/m-bain/whisperX
- PyTorch 2.6 Release Notes: https://pytorch.org/docs/stable/generated/torch.load.html
- WhisperX PR #1313: PyTorch 2.6+ blackwell fix
