# Server Refactoring Progress

## Status: IN PROGRESS

### Completed ✅
1. Created `services/` directory
2. Created `services/streaming_service.py` with:
   - `StreamingOrchestrator` class
   - `_process_block_async` function
   - `ensure_selected_parts_is_dict` utility function

### In Progress 🔄
1. Extracting large streaming functions (`generate_design_stream`, `refine_design_stream`, `answer_question`) to `services/streaming_service.py`
2. Creating `routes/streaming.py` for SSE endpoints
3. Creating `routes/eda.py` for EDA asset endpoints
4. Creating `routes/forecast.py` for forecast endpoints
5. Removing duplicate route definitions from `server.py`
6. Cleaning up `server.py` to ~150 lines

### Remaining Tasks 📋
1. Move `generate_design_stream` (500+ lines) to streaming_service.py
2. Move `refine_design_stream` (100+ lines) to streaming_service.py
3. Move `answer_question` (100+ lines) to streaming_service.py
4. Create `routes/streaming.py` with `/mcp/component-analysis` endpoint
5. Create `routes/eda.py` with all `/api/eda/*` endpoints
6. Create `routes/forecast.py` with all `/api/forecast/*` endpoints
7. Remove inline route definitions (lines 68-213) from server.py
8. Remove fallback route definitions (lines 226-395) from server.py
9. Remove emergency route definitions (lines 375-396) from server.py
10. Remove legacy endpoints (lines 2106-2419) from server.py
11. Remove duplicate CORS middleware (lines 691-697)
12. Simplify route registration logic (lines 44-658)
13. Create `api/middleware/__init__.py` for centralized middleware setup
14. Update `routes/__init__.py` to include new route modules
15. Test all endpoints to ensure nothing broke

### Notes
- The streaming functions are very large and complex. They should be moved carefully.
- The route registration logic has multiple fallback layers that need to be simplified.
- Many legacy endpoints use `Request` instead of Pydantic models - this should be fixed in a follow-up.

