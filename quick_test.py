"""Quick test to see the actual error."""
import requests
import json

url = "http://localhost:8080/profiles/parent"
token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtZUTZZTW56VXBYUnk4YjV2alBYSiJ9.eyJpc3MiOiJodHRwczovL2Rldi1qYnJyaXVjNXZ5am1pd3R4LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJhdXRoMHw2OTExNTNlOTM0NjFjZDA1YWRmNDI2NGUiLCJhdWQiOlsiaHR0cHM6Ly9kZXYtamJycml1YzV2eWptaXd0eC51cy5hdXRoMC5jb20vYXBpL3YyLyIsImh0dHBzOi8vZGV2LWpicnJpdWM1dnlqbWl3dHgudXMuYXV0aDAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTc2Mjc1MDE2OSwiZXhwIjoxNzYyODM2NTY5LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIHJlYWQ6Y3VycmVudF91c2VyIHVwZGF0ZTpjdXJyZW50X3VzZXJfbWV0YWRhdGEgZGVsZXRlOmN1cnJlbnRfdXNlcl9tZXRhZGF0YSBjcmVhdGU6Y3VycmVudF91c2VyX21ldGFkYXRhIGNyZWF0ZTpjdXJyZW50X3VzZXJfZGV2aWNlX2NyZWRlbnRpYWxzIGRlbGV0ZTpjdXJyZW50X3VzZXJfZGV2aWNlX2NyZWRlbnRpYWxzIHVwZGF0ZTpjdXJyZW50X3VzZXJfaWRlbnRpdGllcyIsImd0eSI6InBhc3N3b3JkIiwiYXpwIjoiZWgzbGt5UGplakI3ZG5nRmV3dUdwNkZTUDFsNmozOUQifQ.DY4Mb1ksboykzhLJDJrMEA6pVqAZYlGn0wi3p7M20VQpUy3LIe-bIzpqv1O9gwG6k4ElZXAZI0lQTL7E13O_mCUgEA5AWuVszNa8Kqgl_KK9XfN39jlQWRxa_QE2-zCA4evjOhH3jtUmImWw5RFaqXC8MWyxspttbcPTZcoOFRjaHySMqdbdel5IzUsBkrD5XIaVnOj6hvOv4UIj_QVZQJIlSh8FrSx9t4VVyYhe5Q8VsACYrM5DdqvH1uEsRl94q3JiXMGkNPS_2rE-EusJ-mhehr6JudR7EQfsJ3rW00iobiFCrhIxcInSer4UP2xYhHN_uhMwKx8YzQf_k9Z9pA"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "accept": "application/json"
}

data = {"name": "John Doe"}

print("Testing POST /profiles/parent...")
print(f"URL: {url}")
print(f"Headers: {headers}")
print(f"Data: {data}")
print()

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response Text: {response.text if 'response' in locals() else 'No response'}")
