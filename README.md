# F1 Analytics Dashboard

A high-performance telemetry replay dashboard for Formula 1 races, featuring an integrated AI Virtual Race Engineer.

## Features

- **Multi-Tab Engineer Sidebar:** 
  - **Engineer Tab:** AI-powered chat with personalized driver advice.
  - **Race Feed:** Integrated live race control and incident logs.
  - **Insights Tab:** Real-time telemetry analysis including **Tyre Age**, DRS status, and pace trends.
- **Interactive Track Map:** Real-time car positions on a dynamic map. Click any car to follow its telemetry.

## Getting Started

### Prerequisites

- Python 3.10 or higher.
- A Google Gemini API Key (for the AI features).

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sarang997/f1-analytics.git
   cd f1-analytics
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the AI (Optional):**
   Set your Google API key as an environment variable:
   ```bash
   export GOOGLE_API_KEY='your-api-key-here'
   ```

### Running the Dashboard

Launch the dashboard by specifying the year, Grand Prix name, and session type:

```bash
python main.py 2024 Austria R
```
*Note: The first run for a specific session will take a moment to download and process telemetry data.*

## Controls

| Key | Action |
|-----|--------|
| `SPACE` | Play / Pause |
| `LEFT` | Decrease playback speed |
| `RIGHT` | Increase playback speed |
| `ENTER` | Focus Chat / Send message |
| `Mouse Click` | Select driver on map or leaderboard |
| `Mouse Drag` | Seek through race timeline |

## Project Structure

- `src/ui/`: Contains the Arcade-based UI implementation and individual components (Track Map, HUD, Chat).
- `src/processor/`: Logic for fetching, processing, and caching F1 telemetry data.
- `src/utils/`: AI client integration, context building for the LLM, and proactive alert logic.
- `data/`: Local cache for processed telemetry and raw FastF1 data.

## License

MIT
