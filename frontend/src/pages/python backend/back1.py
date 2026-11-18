from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "hello world"}

@app.put("/")
def readuser():
    return{"holq":"okk"}

@app.get("/items/{item_id}")
def read_item(item_id):
    return{"item id ":item_id}
