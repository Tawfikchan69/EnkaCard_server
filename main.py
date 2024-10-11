from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import enkanetwork
import enkacard
import uvicorn
import starrailcard
import concurrent.futures
from io import BytesIO
import requests

app = FastAPI()

# Genshin Card Generator
async def card2(id, designtype):
    async with enkacard.ENC(uid=str(id)) as encard:
        return await encard.creat(template=(2 if str(designtype) == "2" else 1))

# Star Rail Card Generator
async def card(id, designtype):
    async with starrailcard.Card() as card:
        return await card.create(uid=str(id), style=(2 if str(designtype) == "2" else 1))

# Image processing functions
def upload_image(data):
    url = "https://fighter-programmer-uploader.hf.space/upload"
    files = {'file': ('file', data, "image/png")}
    response = requests.post(url, files=files)

    if response.status_code != 200:
        raise Exception(f"HTTP Error: {response.status_code}")

    body = response.json()
    if body["url"]:
        return body["url"]
    else:
        raise Exception(f"Telegraph error: {body.get('error', 'Unknown error')}")

def process_image(dt):
    with BytesIO() as byte_io:
        dt.card.save(byte_io, "PNG")
        byte_io.seek(0)
        image_url = upload_image(byte_io)

        return {
            "name": dt.name,
            "url": image_url
        }

def process_images(result):
    characters = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_image, dt) for dt in result.card]

        for future in concurrent.futures.as_completed(futures):
            try:
                characters.append(future.result())
            except Exception as e:
                print(f"Error processing image: {e}")

    return characters

# Routes
@app.get("/{id}")
async def genshin_characters(id: int, design: str = "1"):
    try:
        result = await card2(id, design)
        characters = process_images(result)
        return JSONResponse(content={'response': characters})

    except enkanetwork.exception.VaildateUIDError:
        return JSONResponse(content={'error': 'Invalid UID. Please check your UID.'}, status_code=400)

    except enkacard.enc_error.ENCardError:
        return JSONResponse(content={'error': 'Enable display of the showcase in the game or add characters there.'}, status_code=400)

    except Exception as e:
        return JSONResponse(content={'error': 'UNKNOWN ERR: ' + str(e)}, status_code=500)

@app.get("/starrail/{id}")
async def starrail_characters(id: int, design: str = "1"):
    try:
        result = await card(id, design)
        characters = process_images(result)
        return JSONResponse(content={'response': characters})

    except Exception as e:
        return JSONResponse(content={'error': 'UNKNOWN ERR: ' + str(e)}, status_code=500)

@app.get("/")
def hello_world():
    return 'AMERICA YA HALLO!!'

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860, workers=8, timeout_keep_alive=60000)
