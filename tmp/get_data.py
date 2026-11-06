import os
import subprocess
import atexit
import time
from pymongo import MongoClient
from bson.json_util import dumps

def main():
    ssh_process = open_tunnel()
    get_data()
    close_tunnel(ssh_process)

def get_data():
    client = MongoClient()
    db = client['tracker']
    collection = db['days']
    cursor = collection.find({})
    documents = list(cursor)
    client.close()
    jsonify_data = dumps(documents, ensure_ascii=False, indent=4)
    base_path = os.path.dirname(__file__)
    os.chdir(base_path)
    with open('data.json', 'w') as file:
        file.write(jsonify_data)

def open_tunnel():
    ssh_process = subprocess.Popen(
        ['ssh', '-L', '27017:localhost:27017', 'myfirstvps', '-N'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    atexit.register(lambda: ssh_process.terminate())
    time.sleep(2)
    return ssh_process

def close_tunnel(ssh_process):
    ssh_process.terminate()
    ssh_process.wait(timeout=5)

if __name__ == '__main__':
    main()