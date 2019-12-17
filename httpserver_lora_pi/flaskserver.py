from flask import Flask
from flask import request
from flask import render_template
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def recieve_post():
    if request.method == 'POST':
        console.log(request)
    return render_template("index.html") 
