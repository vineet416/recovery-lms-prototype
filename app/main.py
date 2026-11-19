from fastapi import FastAPI

app = FastAPI()


# Shows a hello message so we know the server is running.
@app.get("/")
def hello() -> dict:
    return {"message": "Hello from the Recovery LMS"}
