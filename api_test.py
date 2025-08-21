import requests

BASE_API_URL = "http://Wellys_ChatBot:8000"
user_name = "한솔"


response = requests.post(f"{BASE_API_URL}/start", json={"user_name": user_name})
response.raise_for_status()
print(response.json().get("message", []))

session_id = response.json().get("session_id", "unknown")

print(session_id)
# response = requests.post(
#     f"{BASE_API_URL}/chat",
#     json={
#         "session_id": session_id,
#         "content": "안녕. 너는 누구니?"
#     }
# )
# response.raise_for_status()
# print(response.json().get("message", []))

# response = requests.post(f"{BASE_API_URL}/end", json={"session_id": session_id})
# response.raise_for_status()
# print(response.json().get("message", []))