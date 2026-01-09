from fastapi import FastAPI

app = FastAPI(title="MTG Builder API")


@app.get("/")
async def root():
    return {"message": "Welcome to MTG Builder API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
