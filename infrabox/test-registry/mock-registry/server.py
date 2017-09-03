from flask import Flask, request

app = Flask(__name__)

@app.route('/<path:path>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def all(path):
    return "OK", 200

if __name__ == '__main__':
    app.run()
