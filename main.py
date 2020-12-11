from flask import Flask

app = Flask(__name__)


@app.route('/')
def func():
    return 'Hey there, this is first python program'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=False)