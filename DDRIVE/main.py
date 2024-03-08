from flask import Flask, request, render_template,session, url_for, redirect, send_file
from os.path import exists
from os import listdir, remove, makedirs
from re import match
from config.config import secret_key
import sqlite3
from hashlib import md5
from datetime import datetime, timedelta
from config.otp import send
from random import randint


#sql_connection
def con():
    conn = sqlite3.connect('credentials.db')
    cursor = conn.cursor()
    return conn, cursor

#create DB if not exist
if not exists('credentials.db'):
    conn, cursor = con()
    conn.close()

#flask app creation
app = Flask(__name__)
app.secret_key = secret_key

#route to login/homepage
@app.route('/')
def first_page():
    if 'userid' in session:
        return redirect(url_for('images'))
    else:
        return render_template("login.html")
    
#route to register
@app.route('/signup')
def signup():
    return render_template('register.html')

#route to handle signup page data
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    dob = request.form['dob']
    email = request.form['email']
    mobile = request.form['mobile']
    username = request.form['username']
    password = request.form['password']


    #checking input validation
    pass_pat = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[~!@#$%^&*])[a-zA-Z0-9~!@#$%^&*]+$'
    email_pat = r'\b[a-zA-Z0-9~!@#$%^&*.]+@[a-zA-Z0-9.-]+\.[A-Z|a-z]{2,}+\b'

    if not match(pass_pat,password):
        return render_template("register.html", error="password must contain atleast one upper case, lower case, number and special character")
    
    elif not match(email_pat,email):
        return render_template("register.html", error="invalid email address!")
    
    else:
        #hashing passwd
        hasher = md5()
        hasher.update(password.encode())
        password =  hasher.hexdigest()

        conn, cursor = con()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" and name="userdata" ')
        if not cursor.fetchone():
            #table creation
            cursor.execute('''CREATE TABLE userdata (
                        username TEXT PRIMARY KEY,
                        password TEXT,
                        name TEXT,
                        dob TEXT,
                        email TEXT,
                        mobile INT
                        ) ''')
            #insert data
            cursor.execute(''' INSERT INTO userdata
                        (username,password,name,dob,email,mobile) Values
                            (?,?,?,?,?,?)''', (username,password,name,dob,email,mobile))
            conn.commit()
            conn.close()
            userdirs = ['images','videos','audios','documents','DP']
            for userdir in userdirs:
                makedirs(f'static/userfiles/{username}/{username}_{userdir}')
            return render_template("login.html", error="Registration successful!")
        
        else:
            # conn, cursor = con()
            cursor.execute('SELECT * FROM userdata')
            row = cursor.fetchall()
            if [ i for i in row if username in i]:
                conn.commit()
                conn.close()
                return render_template("register.html", error="username already taken!")
            elif [ i for i in row if email in i]:
                conn.commit()
                conn.close()
                return render_template("register.html", error="email already exists!")
            else:
                #insert data
                cursor.execute(''' INSERT INTO userdata
                            (username,password,name,email,mobile) Values
                                (?,?,?,?,?,?)''', (username,password,name,dob,email,mobile))
                conn.commit()
                conn.close()
                userdirs = ['images','videos','audios','documents','DP']
                for userdir in userdirs:
                    makedirs(f'static/userfiles/{username}/{username}_{userdir}')
                return render_template("login.html", error="Registration successful!")


#login the session for current user
@app.route('/login', methods=['POST'])
def login():
    error = "invalid userid or password!"
    username = request.form['username']
    password = request.form['password']
    
    #hashing passwd
    hasher = md5()
    hasher.update(password.encode())
    password =  hasher.hexdigest()

    conn = sqlite3.connect('credentials.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" and name="userdata"')
    if cursor.fetchone():
        cursor.execute('SELECT * FROM userdata WHERE username=? OR email=?', (username,username,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return render_template("login.html", error='account does not exist!')
        else:
            if row[0] == username or row[4] == username and row[1] == password:
                session['userid'] = username
                session.permanent = True
                conn.close()
                return redirect(url_for('images'))
            else:
                conn.close()
                return render_template("login.html", error=error)
#Reset Password
@app.route('/reset', methods=['GET','POST'])
def reset():
    if request.method == 'GET':
        return render_template('/editProfileInfo/otp.html',error='Get OTP')
    
    if request.method == 'POST':
        email = request.form['email']
        conn, cursor = con()
        cursor.execute('SELECT email FROM userdata')
        emails = cursor.fetchall()

        #check if email is valid
        if [ mail for mail in emails if email in mail]:
            #to get username
            cursor.execute("SELECT username FROM userdata WHERE email=?", (email,))
            row = cursor.fetchone()
            username = row[0]
            conn.close()
            otp = randint(100000, 999999)
            ExpireTime = datetime.now()+timedelta(minutes=10)
            ExpireTime = ExpireTime.strftime('%H:%M')
            session['OTP'] = [otp,email,ExpireTime]
            session.permanent = True
            resetURL = url_for('pass_reset', _external=True)
            #send OTP
            send(email,username,resetURL,otp)
            return render_template('/editProfileInfo/resetPasswd.html', error='Enter 6 digit OTP')
        else:
            return render_template('/editProfileInfo/otp.html', error='Invalid email!')

@app.route('/pass_reset',methods=['GET','POST'])
def pass_reset():
    if 'OTP' in session:
        if request.method == 'POST':
            OTP = session['OTP'][0]
            email = session['OTP'][1]
            ExpireTime = session['OTP'][2]

            ExpireTime = datetime.strptime(ExpireTime,'%H:%M').time()
            currentTime = datetime.now().time()
            password = request.form['password']
            new_password = request.form['new_password']
            user_otp = int(request.form['otp'])

            if ExpireTime > currentTime:
                print('inside')
                if OTP==user_otp:
                    if password==new_password:
                        #checking Password validation
                        pass_pat = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[~!@#$%^&*])[a-zA-Z0-9~!@#$%^&*]+$'
                        if not match(pass_pat,password):
                            return render_template("/editProfileInfo/resetPasswd.html", error="password must contain atleast one upper case, lower case, number and special character")
                        else:
                            #hashing passwd
                            hasher = md5()
                            hasher.update(password.encode())
                            password =  hasher.hexdigest()
                            #update password
                            conn, cursor = con()
                            cursor.execute('UPDATE userdata SET password=? WHERE email=?', (password,email,))
                            conn.commit()
                            conn.close()
                            session.pop('OTP',None)
                            return render_template('login.html',error='password updated!')
                    else:
                        return render_template('/editProfileInfo/resetPasswd.html', error='Paasswords did not match!') 
                else:
                    return render_template('/editProfileInfo/resetPasswd.html', error='Invalid OTP!') 
            else:
                session.pop('OTP', None)
                return render_template('/editProfileInfo/resetPasswd.html', error='OTP Expired!') 
        elif request.method == 'GET':
            ExpireTime = session['OTP'][2]
            ExpireTime = datetime.strptime(ExpireTime,'%H:%M').time()
            currentTime = datetime.now().time()
            if ExpireTime > currentTime:
                return render_template('/editProfileInfo/resetFromEmail.html')
            else:
                session.pop('OTP',None)
                return '''<body style="margin-top: 100px;margin-bottom: 400px;text-align: center;font-size: xx-large;"><p>OTP expired resend OTP or try again later!</p></body>'''
    else:
        return '''<body style="margin-top: 100px;margin-bottom: 400px;text-align: center;font-size:xx-large">
        <p>OTP expired resend OTP or try again later!</p></body>'''

#reseting from email link directly
@app.route('/resetFromEmail',methods=['POST'])
def resetFromEmail():
    if 'OTP' in session:
        email = session['OTP'][1]
        ExpireTime = session['OTP'][2]

        ExpireTime = datetime.strptime(ExpireTime,'%H:%M').time()
        currentTime = datetime.now().time()
        password = request.form['password']
        new_password = request.form['new_password']

        if ExpireTime > currentTime:
            if password==new_password:
                #checking Password validation
                pass_pat = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[~!@#$%^&*])[a-zA-Z0-9~!@#$%^&*]+$'
                if not match(pass_pat,password):
                    return render_template("/editProfileInfo/resetPasswd.html", error="password must contain atleast one upper case, lower case, number and special character")
                else:
                    #hashing passwd
                    hasher = md5()
                    hasher.update(password.encode())
                    password =  hasher.hexdigest()
                    #update password
                    conn, cursor = con()
                    cursor.execute('UPDATE userdata SET password=? WHERE email=?', (password,email,))
                    conn.commit()
                    conn.close()
                    session.pop('OTP',None)
                    return render_template('login.html',error='password updated!')
            else:
                return render_template('/editProfileInfo/resetPasswd.html', error='Paasswords did not match!') 
        else:
            session.pop('OTP',None)
            return '''<body style="margin-top: 100px;margin-bottom: 400px;text-align: center;font-size: xx-large;"><p>OTP expired resend OTP or try again later!</p></body>'''
        
    return '''<body style="margin-top: 100px;margin-bottom: 400px;text-align: center;font-size: xx-large;       "><p>OTP expired resend OTP or try again later!</p></body>'''
    
#sesson routes (login mandatory)
@app.route('/profile')
def profile():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        conn = sqlite3.connect('credentials.db')
        cursor = conn.cursor()
        cursor.execute("SELECT username,name,dob,email,mobile FROM userdata WHERE username=?",(username,))
        row = cursor.fetchone()
        conn.close()
        DP = f'userfiles/{username}/{username}_DP/DP.png'
        return render_template('profile.html',username=row[0],name=row[1],dob=row[2],email=row[3],mobile=row[4], DP=DP)

@app.route('/edit', methods=['GET','POST'])
def edit():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        DP = f'userfiles/{username}/{username}_DP/DP.png'
        if request.method=='GET':
            if request.args.get('name'):
                return render_template('/editProfileInfo/nameEdit.html',DP=DP,status='name')
            
            elif request.args.get('dob'):
                return render_template('/editProfileInfo/editDoB.html',DP=DP,status='dob')
            
            elif request.args.get('email'):
                return render_template('/editProfileInfo/emailEdit.html',DP=DP,status='email')
            
            elif request.args.get('mobile'):
                return render_template('/editProfileInfo/mobileEdit.html',DP=DP,status='mobile')
            else:
                conn,cursor = con()
                cursor.execute("SELECT username,name,dob,email,mobile FROM userdata WHERE username=?",(username,))
                row = cursor.fetchone()
                conn.close()
                return render_template('/editProfileInfo/edit.html',username=row[0],name=row[1],dob=row[2],email=row[3],mobile=row[4], DP=DP)
            
        elif request.method=='POST':
            conn,cursor = con()
            if request.args.get('name'):
                name = request.form['name']
                cursor.execute('UPDATE userdata SET name=? WHERE username=?',(name,username,))

            elif request.args.get('dob'):
                dob = request.form['dob']
                cursor.execute('UPDATE userdata SET dob=? WHERE username=?',(dob,username,))

            elif request.args.get('email'):
                email = request.form['email']
                email_pat = r'\b[a-zA-Z0-9~!@#$%^&*.]+@[a-zA-Z0-9.-]+\.[A-Z|a-z]{2,}+\b'

                if not match(email_pat,email):
                    return render_template("/editProfileInfo/emailEdit.html",DP=DP,status='invalid email')
                
                else:
                    cursor.execute('UPDATE userdata SET email=? WHERE username=?',(email,username,))

            elif request.args.get('mobile'):
                mobile = request.form['mobile']
                cursor.execute('UPDATE userdata SET mobile=? WHERE username=?',(mobile,username,))

            else:
                conn.commit()
                conn.close()
                return ' something went wrong!'
            
            conn.commit()
            conn.close()
            return redirect('/edit')


#DPupdate
@app.route('/updateDP',methods=['GET','POST'])
def updateDP():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        DP = f'userfiles/{username}/{username}_DP/DP.png'
        if request.method == 'GET':
            status ='choose a picture!'
            return render_template('/editProfileInfo/updateDP.html',status=status,DP=DP)
        
        elif request.method == 'POST':
            file = request.files['file']
            filename = file.filename.lower()
            filename = filename.lower()
            type = ''
            images = ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg']

            if [ extension for extension in images if extension in filename]:
                type = 'images'
                file.save(f'static/userfiles/{username}/{username}_DP/'+'DP.png')
                return render_template("/editProfileInfo/updateDP.html", status=f"Profile picture updated!",DP=DP)
            else:
                status ='choose a valid picture!'
                return render_template('/editProfileInfo/updateDP.html',status=status,DP=DP)

# @app.route('/home')
# def home():
#     username = session['userid']
#     path = f'userfiles/{username}/{username}_images/'
#     files = listdir(f'static/{path}')
#     status =f'welcome back {username}!'
#     return render_template('index.html',files=files,path=path,status=status)
#     # return render_template("index.html", user=f'welcome back {username}!',images=images)

@app.route('/images')
def images():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        path = f'userfiles/{username}/{username}_images/'
        page_num = int(request.args.get("page_num",1))
        total_files = listdir(f'static/{path}')
        total_count = len(total_files)
        per_page = 50
        last_page_num = total_count/per_page

        if not isinstance(last_page_num,int):
            last_page_num=int(last_page_num)+1
        if page_num>=last_page_num:
            page_num=last_page_num
        if page_num==0:
            page_num=1
        first_file = (page_num -1)*per_page
        last_file = first_file+per_page
        files = total_files[first_file:last_file]

        if total_count==0:
            return render_template('/imageOperations/images.html',files=files,path=path,page_num=page_num)
        else:
            if page_num<last_page_num:
                return render_template('/imageOperations/images.html',files=files,path=path,page_num=page_num)
            elif page_num==last_page_num:
                return render_template('/imageOperations/images.html',files=files,path=path,page_num=page_num)
            else:
                page_num=page_num-1
                return render_template('/imageOperations/images.html',files=files,path=path,page_num=page_num, status='no more files!')


@app.route('/videos')
def videos():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        path = f'userfiles/{username}/{username}_videos/'
        page_num = int(request.args.get("page_num",1))
        total_files = listdir(f'static/{path}')
        total_count = len(total_files)
        per_page = 5
        last_page_num = total_count/per_page

        if not isinstance(last_page_num,int):
            last_page_num=int(last_page_num)+1
        if page_num>=last_page_num:
            page_num=last_page_num
        if page_num==0:
            page_num=1
        first_file = (page_num -1)*per_page
        last_file = first_file+per_page
        files = total_files[first_file:last_file]

        if total_count==0:
            return render_template('/videoOperations/videos.html',files=files,path=path,page_num=page_num)
        else:
            if page_num<last_page_num:
                return render_template('/videoOperations/videos.html',files=files,path=path,page_num=page_num)
            elif page_num==last_page_num:
                return render_template('/videoOperations/videos.html',files=files,path=path,page_num=page_num)
            else:
                page_num=page_num-1
                return render_template('/videoOperations/videos.html',files=files,path=path,page_num=page_num, status='no more files!')

@app.route('/stream')
def stream():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        fullpath = request.args.get('fullpath')
        page_num = request.args.get('page_num')
        file = fullpath.removeprefix(f"/static/userfiles/{username}/{username}_videos/")
        path = f'userfiles/{username}/{username}_videos/'
        return render_template('/videoOperations/stream.html',file=file,path=path,page_num=page_num)

@app.route('/audios')
def audios():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        path = f'userfiles/{username}/{username}_audios/'
        # files = listdir(f'static/{path}')
        page_num = int(request.args.get("page_num",1))
        total_files = listdir(f'static/{path}')
        total_count = len(total_files)
        per_page = 30
        last_page_num = total_count/per_page

        if not isinstance(last_page_num,int):
            last_page_num=int(last_page_num)+1
        if page_num>=last_page_num:
            page_num=last_page_num
        if page_num==0:
            page_num=1
        first_file = (page_num -1)*per_page
        last_file = first_file+per_page
        files = total_files[first_file:last_file]

        if total_count==0:
            return render_template('/audioOperations/audios.html',files=files,path=path,page_num=page_num)
        else:
            if page_num<last_page_num:
                return render_template('/audioOperations/audios.html',files=files,path=path,page_num=page_num)
            elif page_num==last_page_num:
                return render_template('/audioOperations/audios.html',files=files,path=path,page_num=page_num)
            else:
                page_num=page_num-1
                return render_template('/audioOperations/audios.html',files=files,path=path,page_num=page_num, status='no more files!')
        return render_template('/audioOperations/audios.html',files=files,path=path,status='')
@app.route('/play')
def play():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        fullpath = request.args.get('fullpath')
        file = fullpath.removeprefix(f"/static/userfiles/{username}/{username}_audios/")
        path = f'userfiles/{username}/{username}_audios/'
        return render_template('/audioOperations/play.html',file=file, path=path)

@app.route('/documents')
def documents():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        path = f'userfiles/{username}/{username}_documents/'
        page_num = int(request.args.get("page_num",1))
        total_files = listdir(f'static/{path}')
        total_count = len(total_files)
        per_page = 20
        last_page_num = total_count/per_page

        if not isinstance(last_page_num,int):
            last_page_num=int(last_page_num)+1
        if page_num>=last_page_num:
            page_num=last_page_num
        if page_num==0:
            page_num=1
        first_file = (page_num -1)*per_page
        last_file = first_file+per_page
        files = total_files[first_file:last_file]

        if total_count==0:
            return render_template('/docsOperations/documents.html',files=files,path=path,page_num=page_num)
        else:
            if page_num<last_page_num:
                return render_template('/docsOperations/documents.html',files=files,path=path,page_num=page_num)
            elif page_num==last_page_num:
                return render_template('/docsOperations/documents.html',files=files,path=path,page_num=page_num)
            else:
                page_num=page_num-1
                return render_template('/docsOperations/documents.html',files=files,path=path,page_num=page_num, status='no more files!')
        return render_template('/docsOperations/documents.html',files=files,path=path,status='')
@app.route('/docview')    
def docview():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        fullpath = request.args.get('fullpath')
        page_num = request.args.get('page_num')
        file = fullpath.removeprefix(f"/static/userfiles/{username}/{username}_documents/")
        path = f'userfiles/{username}/{username}_documents/'
        return render_template('/docsOperations/docview.html',file=file, path=path,page_num=page_num)

#upload
@app.route('/upload',methods=['POST'])
def uplaod():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        DP = f'userfiles/{username}/{username}_DP/DP.png'
        files = request.files.getlist('files[]')
        for file in files:
            filename = file.filename
            filename = filename.lower()
            type = ''
            index = filename.rindex('.')
            format = filename[index:]
            time = datetime.now()
            time = time.strftime("%y%m%d%H%M")
            name = ''
            print(filename)
            for i in filename:
                if len(name)==20:
                    break
                elif i.isalpha():
                    name += i
                elif i.isdigit():
                    name += i
                elif i =='.':
                    break
                else:
                    name += '_'

            audios = ['.mp3', '.m4a', '.wav', '.aiff', '.aif', '.flac', '.ogg', '.aac']

            videos = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.mpeg', '.mpg']

            images = ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg']

            if [ extension for extension in audios if extension in filename]:
                type = 'audios'
                format = '.mp3'
            elif [ extension for extension in videos if extension in filename]:
                type = 'videos'
            elif [ extension for extension in images if extension in filename]:
                type = 'images'
            else:
                type = 'documents'

            name = time+name+format
            file.save(f'static/userfiles/{username}/{username}_{type}/'+name)
        return render_template("upload.html", status=name,DP=DP)


@app.route('/open')
def open():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        file = request.args.get('file')
        path = file.removeprefix('/static/')
        filename = file.removeprefix(f'/static/userfiles/{username}/{username}_images/')
        return render_template('/imageOperations/download.html', path=path,filename=filename)

@app.route('/download')
def download():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        file = request.args.get('filepath')
        file = f'static/{file}'
        return send_file(file, as_attachment=True)

@app.route('/delete')
def delete():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        file = request.args.get('filepath')
        page_num = request.args.get('page_num')
        file = f'static/{file}'
        type = ''
        try:
            if exists(file):
                remove(file)
        except Exception as e:
            return " <p>stop the videos first!</p>"
        
        if 'videos' in file:
            type='videos'
        elif 'audios' in file:
            type='audios'
        elif 'images' in file:
            type='images'
        else:
            type='documents'
        return redirect(url_for(f'{type}',page_num=page_num))

@app.route('/upform')
def upform():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        username = session['userid']
        DP = f'userfiles/{username}/{username}_DP/DP.png'
        return render_template("upload.html",DP=DP)

@app.route('/about')
def about():
    if "userid" not in session:
        return render_template("login.html",error="Please log in!")
    else:
        return render_template('about.html')

#route to logout
@app.route('/logout')
def logout():
    session.pop('userid', None)
    return render_template('login.html',error='logged out successfully!')


if __name__=="__main__":
    app.run(debug=True,host='0.0.0.0')