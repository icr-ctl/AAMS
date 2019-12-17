import requests
import time

URL = "http://192.168.10.10:8080/api/devices/38a91010c8753276/events"
h={"Accept":"application/json", "Grpc-Metadata-Authorization":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsb3JhLWFwcC1zZXJ2ZXIiLCJhdWQiOiJsb3JhLWFwcC1zZXJ2ZXIiLCJuYmYiOjE1MDAwMDAwMDAsImV4cCI6MTY1MDAwMDAwMCwic3ViIjoidXNlciIsInVzZXJuYW1lIjoiYWRtaW4ifQ.1IluGjVoyB_zDDhueazk2bF5j0ZpeaIXjSvDzhMs5Yk"}
p={}
r = requests.get(url=URL, headers=h, params=p, stream=True)
data = r.json()
print(data)
