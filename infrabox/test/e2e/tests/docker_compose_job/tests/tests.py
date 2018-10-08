import requests

def test_get():
    print("get")
    r = requests.get("http://test-server:3000")
    print(r.json())
    assert True
