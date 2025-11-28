# Project Structure

This is a clean, organized structure for the RKL Secure Reasoning Brief project.

```
secure-reasoning-brief-clean/
├── config/              # System & agent configurations
│   ├── agents/          # YAML configs for each agent
│   └── config.yaml      # Main configuration
├── scripts/             # Pipeline execution scripts
│   ├── run_pipeline.py  # Main pipeline orchestrator
│   ├── gemini_client.py # Gemini API client
│   └── ...              # Other utility scripts
├── rkl_logging/         # Research telemetry library
│   ├── __init__.py
│   └── structured_logger.py
├── data/
│   └── sample_briefs/   # Example output briefs (last 3)
├── datasets/
│   └── telemetry-v1.0/  # Published telemetry dataset (HuggingFace)
├── docs/                # Additional documentation
├── video/               # Demo video and production assets
│   ├── graphics/        # Final presentation graphics
│   ├── audio/           # Final audio narration files
│   ├── demo_video_final.mp4  # Final demo video
│   └── RECORDING_TRANSCRIPT_v2.txt
├── competition_submission/  # Kaggle competition docs
├── README.md            # Main project README
├── ARCHITECTURE.md      # Detailed system architecture
├── requirements.txt     # Python dependencies
└── .gitignore

## Original Project Location

The original working directory is preserved at:
`/home/mike/project/rkl-consolidated/secure-reasoning-brief/`

This clean copy contains only the essential files for submission.
