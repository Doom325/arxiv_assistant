from google import genai; client = genai.Client(api_key='AIzaSyA4qTEczFnPBRYvAVfs-5FMxPk28hSj5Is'); print([m.name for m in client.models.list() if 'flash' in m.name.lower()])
