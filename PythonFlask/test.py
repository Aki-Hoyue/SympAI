import time

from flask import Flask, Response
app = Flask(__name__)

@app.route('/stream')
def stream_numbers():
    def generate_numbers():
        for number in range(1, 10):
            yield f"{number}\n"  # 每次生成一个数字就发送 \n 最好不要删除
            time.sleep(0.5)  # 为了演示，加入短暂延迟

    return Response(generate_numbers())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)