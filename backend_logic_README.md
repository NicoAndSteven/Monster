# Monster AI Backend Logic

This document describes the backend implementation for the Monster AI platform. The backend provides API support for the frontend features, including Data Dashboard, Novel Management, and Asset Center.

## Technology Stack

- **Language**: Python 3.8+
- **Framework**: FastAPI (for high-performance async APIs)
- **Data Storage**: Local JSON file storage (simulating a database for portability)

## API Endpoints

### 1. Dashboard (`/api/dashboard`)

- **GET /api/dashboard/stats**
  - **Purpose**: Returns aggregated statistics for the Overview page.
  - **Logic**: 
    - Scans the `storage/` directory for all JSON files.
    - Aggregates word counts, chapter counts, and novel counts.
    - Reads `pipeline_status.json` to get the current state of the task pipeline (dynamic status).
    - Returns mock analytics data for charts (distribution, etc.).

- **POST /api/pipeline/update**
  - **Purpose**: Updates the current task pipeline status.
  - **Body**: `PipelineStatus` (status, current_stage, progress, task_name)
  - **Logic**: Saves the new status to `pipeline_status.json`, allowing the frontend to reflect changes dynamically.

### 2. Novels (`/api/novels`)

- **GET /api/novels**
  - **Purpose**: Lists all created novels.
  - **Logic**: Scans `storage/novel_*.json` files (excluding chapters) and returns metadata.

- **POST /api/novels**
  - **Purpose**: Creates a new novel.
  - **Logic**: Saves novel metadata to `storage/novel_{id}.json`.

- **POST /api/novels/{id}/generate**
  - **Purpose**: Generates a new chapter using AI logic.
  - **Logic**: 
    - Uses `novel_generator` service (currently mock/template-based).
    - Saves the generated content to `storage/novel_{id}_chapter_{num}.json`.

### 3. Assets (`/api/assets`)

- **GET /api/assets**
  - **Purpose**: Lists all assets (characters, scenes, audio, video).
  - **Logic**: Reads from `storage/assets.json`.

- **POST /api/assets**
  - **Purpose**: Adds a new asset.
  - **Logic**: Appends the new asset to `storage/assets.json`.

- **PUT /api/assets/{id}**
  - **Purpose**: Updates an existing asset (e.g., editing a character).
  - **Logic**: Finds the asset by ID in `storage/assets.json` and updates it.

- **DELETE /api/assets/{id}**
  - **Purpose**: Deletes an asset.
  - **Logic**: Removes the asset from `storage/assets.json`.

## Directory Structure

- `backend/main.py`: Entry point and API route definitions.
- `backend/models/`: Pydantic models for data validation.
- `backend/services/`: Business logic (dashboard stats, text generation).
- `backend/utils/`: Helper functions (file storage operations).
- `storage/`: JSON files acting as the database.

## Running the Backend

1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Run the server:
   ```bash
   python backend/main.py
   ```
   The server will start at `http://0.0.0.0:8000`.

## Integration with Frontend

The frontend (Vue.js) communicates with these APIs via `fetch` or `axios`. 
- **Data Dashboard**: Calls `/api/dashboard/stats` on mount.
- **Workbench**: Should call `/api/novels` to sync novel list.
- **Asset Center**: Should call `/api/assets` to sync characters and media.

(Note: Currently, the frontend implementation includes fallback mock data to ensure the UI works even if the backend is offline.)
