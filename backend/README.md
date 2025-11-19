# AIToday Backend

This is the backend for the AIToday news aggregator, built with FastAPI and Python.

## Features
- **Data Collection**: Fetches data from YouTube, X (Twitter), Reddit, and RSS feeds.
- **AI Processing**: Uses OpenAI to translate titles to Chinese and summarize content.
- **Hotspot Generation**: Clusters high-heat items into trending events.
- **API**: Provides endpoints for the frontend to consume feed and hotspot data.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    # OR if using poetry
    poetry install
    ```
    *Note: A `pyproject.toml` is provided.*

2.  **Environment Variables**:
    Create a `.env` file in the `backend` directory with the following:
    ```env
    OPENAI_API_KEY=your_openai_key
    YOUTUBE_API_KEY=your_youtube_key
    TWITTER_BEARER_TOKEN=your_twitter_token
    REDDIT_CLIENT_ID=your_reddit_id
    REDDIT_CLIENT_SECRET=your_reddit_secret
    
    POSTGRES_SERVER=localhost
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=password
    POSTGRES_DB=aitoday
    ```

3.  **Configuration**:
    Edit `sources.yaml` to configure the channels, users, and feeds you want to track.

4.  **Run the Server**:
    ```bash
    uvicorn app.main:app --reload
    ```

## API Documentation
Once running, visit `http://localhost:8000/docs` for the interactive API documentation.
