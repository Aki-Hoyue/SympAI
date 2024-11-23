from flask_cors import CORS
from flask import Flask, jsonify, request, Response
import time
import json
app = Flask(__name__)
CORS(app)

sample_text=['Why ','are ','you ','a ','nigger?']

# 只用这个函数
@app.route('/api/tasks', methods = ['POST'])
def post_tasks():
    if request.headers['Content-Type'] == 'application/json':
        data = request.get_json()
    id = data['id']
    messages = data['messages']
    mesLen = len(messages)
    reMessage = messages[mesLen-1]['content']
    print(id, reMessage)
    def generate_numbers():
        for str in sample_text:
            yield f"{str}"  
            time.sleep(0.5)  
    return Response(generate_numbers(),mimetype="text/plain")

# @app.route('/stream')
# def stream_numbers():
#     def generate_numbers():
#         for number in sample_text:
#             yield f"{number}\n"  
#             time.sleep(0.5)  

#     return Response(generate_numbers())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)