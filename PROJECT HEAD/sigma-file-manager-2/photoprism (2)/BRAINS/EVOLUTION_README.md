# Sorting Hat Evolution System

The Evolution System is a self-improving component that learns from your file organization preferences to make increasingly better recommendations over time.

## How It Works

1. **Pattern Recognition**: The system tracks your file organization decisions and identifies patterns.
2. **Learning**: It learns from your feedback to improve future recommendations.
3. **Adaptation**: As you interact with it, the system evolves to better match your organizational style.

## Key Components

- **Pattern Tracking**: Records file extension -> directory mappings
- **Feedback System**: Collects your input on recommendations
- **Evolution Engine**: Analyzes patterns to improve recommendations

## Getting Started

### 1. Initialize the System

Run the initialization script to set up the evolution database:

```bash
python initialize_evolution.py
```

This creates:
- A safe operating folder at `~/OrganizeFolder`
- An evolution database at `./data/evolution.db`
- Default patterns to kickstart the learning process

### 2. Run the Server

Start the FastAPI server:

```bash
uvicorn server:app --reload
```

### 3. Use the Evolution Dashboard

Open `evolution_dashboard.html` in your browser to monitor and manage the evolution system.

## Adding Feedback

When you receive file organization recommendations, you can provide feedback in three ways:

1. **Accept**: Use the recommendation as-is
2. **Reject**: Keep the file where it is
3. **Custom**: Specify your preferred organization

Each piece of feedback helps the system learn your preferences.

## Evolution Process

The evolution process runs automatically as you interact with the system, but you can also trigger it manually from the dashboard.

During evolution:
1. The system analyzes past recommendations
2. Extracts common patterns
3. Updates confidence scores
4. Improves future recommendations

## Safety Features

- The system only operates on files within the designated safe folder
- GitHub repositories are automatically protected
- All operations require explicit confirmation

## Technical Details

- **Database**: SQLite database storing patterns and feedback
- **Learning Algorithm**: Confidence-weighted pattern matching
- **API Endpoints**: RESTful endpoints for feedback and evolution

## Monitoring Progress

Use the Evolution Dashboard to:
- View current organizational patterns
- See acceptance rates and metrics
- Trigger manual evolution
- Review AI-generated insights
