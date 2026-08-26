# Auto Parts Classification & Labeling System

Automated computer vision and labeling pipeline designed for robotic warehouse complexes to classify and manage used auto parts.

## Tech Stack & Architecture
- **Language:** Python 3.10+
- **Object Detection & Classification:** YOLOv8 / YOLOv11 (Ultralytics)
- **Database & Storage:** SQLite (`warehouse.db`)
- **Core Modules:**
  - `detector.py` / `main.py` — Real-time inference and integration pipeline.
  - `train.py` — Model fine-tuning and validation pipeline.
  - `database.py` / `create_database.py` — Relational schema for inventory logging.
  - `help_scripts/` — Dataset preprocessing, auto-labeling, and splitting utilities.

## Setup & Execution
1. Clone repository:
   ```bash
   git clone [https://github.com/Deda3d/AutoPartsClassification2.git](https://github.com/Deda3d/AutoPartsClassification2.git)
   cd AutoPartsClassification2