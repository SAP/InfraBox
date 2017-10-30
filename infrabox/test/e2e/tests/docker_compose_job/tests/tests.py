import requests

def test_get():
    print "get"
    r = requests.get("http://server:3000")
    print r.json()
    assert True