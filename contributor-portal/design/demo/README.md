# Demo Content — Real-World Company Profiles + Annotation Campaigns

Assets for populating the Contributor Kitchen demo with realistic company profiles and annotation campaigns. All logos sourced from GitHub/HuggingFace org avatars; descriptions adapted from each company's own public "About" text.

## Company Matrix

### Big Tech

| Company | Frontier | Logo | HF Org | Source |
|---|---|---|---|---|
| [NVIDIA](companies/nvidia-physicalai/) | Robotics | `logo.png` (3.5 KB) | [nvidia](https://huggingface.co/nvidia) — 755 models, 221 datasets | HF avatar |
| [Google DeepMind](companies/google-deepmind/) | Robotics + Language | `logo.png` (7.1 KB) | [google](https://huggingface.co/google) — 1,092 models, 68 datasets | HF avatar |
| [Alibaba DAMO Academy](companies/alibaba-damo/) | Vision + Language | `logo.png` (26.8 KB) | [DAMO-NLP-SG](https://huggingface.co/DAMO-NLP-SG) — 55 models, 15 datasets | GitHub avatar |
| [Meta FAIR](companies/meta-fair/) | Embodied AI + Language | `logo.png` (1.1 KB) | [facebook](https://huggingface.co/facebook) — 2,314 models, 111 datasets | HF avatar |

### Emerging

| Company | Frontier | Logo | HF Org | Source |
|---|---|---|---|---|
| [Physical Intelligence](companies/physical-intelligence/) | Robotics | `logo.png` (3.0 KB) | via [lerobot](https://huggingface.co/lerobot) (π0 models) | GitHub avatar |
| [Figure AI](companies/figure-ai/) | Robotics | `logo.png` (1.5 KB) | [FigureAI](https://huggingface.co/FigureAI) — verified, 0 public models | GitHub avatar |
| [ElevenLabs](companies/eleven-labs/) | Speech | `logo.png` (674 B) | [elevenlabs](https://huggingface.co/elevenlabs) — 1 model | GitHub avatar |
| [Mistral AI](companies/mistral-ai/) | Language | `logo.png` (2.7 KB) | [mistralai](https://huggingface.co/mistralai) — 71 models, 4 datasets | HF avatar |

### Small / Academic

| Company | Frontier | Logo | HF Org | Source |
|---|---|---|---|---|
| [Stanford IRIS Lab](companies/stanford-iris/) | Robotics | `logo.png` (7.9 KB) | — | GitHub avatar |
| [1X Technologies](companies/1x-technologies/) | Robotics | `logo.png` (3.8 KB) | — | GitHub avatar |

## Campaign List

10 campaigns, each aligned to a company's real-world data needs:

| Campaign | Company | Frontier | Compensation | Tasks |
|---|---|---|---|---|
| [Kitchen Manipulation](campaigns/nvidia-kitchen-manipulation.json) | NVIDIA | Robotics | Fixed ($2.50/$1.50) | Supply → VE → Label → Validate |
| [Dexterous Grasping](campaigns/pi-dexterous-grasping.json) | Physical Intelligence | Robotics | Royalty | Supply → Label → Validate |
| [Humanoid Locomotion](campaigns/figure-humanoid-locomotion.json) | Figure AI | Robotics | Fixed ($3.00/$2.00) | Supply → VE → Label → Validate |
| [Multi-Modal Instructions](campaigns/deepmind-instruction-following.json) | Google DeepMind | Vision + Lang | Fixed ($1.00/$0.75) | Supply → Label → Validate |
| [Expressive Speech](campaigns/elevenlabs-expressive-speech.json) | ElevenLabs | Speech | Hybrid ($0.50 + royalty) | Supply → Label → Validate |
| [Product Visual QA](campaigns/damo-product-visual-qa.json) | Alibaba DAMO | Vision + Lang | Fixed ($0.80/$0.60) | Supply → Label → Validate |
| [Instruction Preferences](campaigns/mistral-instruction-preference.json) | Mistral AI | Language | Fixed ($1.25) | Label → Validate |
| [Embodied Navigation](campaigns/fair-embodied-navigation.json) | Meta FAIR | Embodied AI | Fixed ($2.00/$1.75) | Supply → VE → Label → Validate |
| [Contact-Rich Manipulation](campaigns/iris-contact-manipulation.json) | Stanford IRIS | Robotics | Bounty ($5K/500) | Supply → Label → Peer Review |
| [Humanoid Daily Tasks](campaigns/1x-humanoid-daily-tasks.json) | 1X Technologies | Robotics | Hybrid ($1.50 + royalty) | Supply → VE → Label → Validate |

## Compensation models represented

| Model | Campaigns | Description |
|---|---|---|
| Fixed | 5 | Per-instance payout on acceptance |
| Royalty | 1 | Revenue share per downstream model training run |
| Hybrid | 2 | Base rate + royalty component |
| Bounty | 1 | Prize pool divided among contributors meeting target |

## Frontier coverage

| Frontier | Campaigns |
|---|---|
| Robotics | 5 (Kitchen, Grasping, Locomotion, Contact, Daily Tasks) |
| Vision + Language | 2 (Instructions, Product VQA) |
| Speech | 1 (Expressive Speech) |
| Language | 1 (Instruction Preferences) |
| Embodied AI | 1 (Navigation) |

## Usage

These JSON files are consumed by the seed script (`packages/api/scripts/seed_campaigns.py`, TBD in I0-4/IN-73):

```python
import json
from pathlib import Path

demo_dir = Path("design/demo")

# Load all company profiles
companies = {}
for p in (demo_dir / "companies").iterdir():
    if (p / "profile.json").exists():
        companies[p.name] = json.loads((p / "profile.json").read_text())

# Load all campaigns
campaigns = []
for f in (demo_dir / "campaigns").glob("*.json"):
    campaigns.append(json.loads(f.read_text()))

# Seed: create org → campaign → tasks for each
for campaign in campaigns:
    company = companies[campaign["company"]]
    # ... insert into Supabase
```

Logo files are copied to `public/assets/demo/orgs/{slug}.png` during seed for Next.js `<Image>` access.
