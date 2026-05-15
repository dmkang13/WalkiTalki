# WalkiTalki MVP

WalkiTalki MVP is a small photo-language-agent prototype:

- React frontend in `frontend/`
- FastAPI backend in `backend/`
- User-provided OpenAI API keys are held only for the current prototype session
- Published agents can be shared by direct link
- Camera capture and image upload both send images through the same lesson flow

## Compile Checks

Frontend:

```bash
cd frontend
npm install
npm run build
```

Backend:

```bash
cd backend
python -m compileall app
```

## Runtime Notes

The backend expects `DATABASE_URL` for PostgreSQL in a real run. If it is absent,
the local development code may use a SQLite fallback so imports and basic local
execution remain lightweight.
