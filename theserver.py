from flask import Flask, render_template, request, abort, redirect, url_for, flash, json
import shlex, configparser, random, hashlib
import cmdparse
from flask_pymongo import PyMongo
from bson import ObjectId
from urllib.parse import quote as urlquote

app = Flask(__name__)

cfg = configparser.ConfigParser()

cfg.read('server.ini')

app.config['SECRET_KEY'] = cfg['general']['SECRET_KEY']

admin_passhash = cfg['general'].get('admin_passhash', hashlib.sha256(cfg['general']['SECRET_KEY'].encode()).hexdigest())

if cfg['mongodb'].get('url')!=None:
    app.config["MONGO_URI"] = cfg['mongodb']['url']
else:
    app.config["MONGO_URI"] = "mongodb://"+ (f"{urlquote(cfg['mongodb'].get('login'),'')}:{urlquote(cfg['mongodb'].get('password'))}@" if cfg['mongodb'].get('login')!=None or cfg['mongodb'].get('password')!=None else '') + f"{cfg['mongodb'].get('ip', 'localhost')}:{cfg['mongodb'].get('port','27017')}/{cfg['mongodb']['db']}"

mongo= PyMongo(app)

app.app_context().push()



@app.route('/quiz', methods=["POST", "GET"])
def startquiz():
    if request.method == 'POST':
        types=request.form.getlist('filters')

        if len(types) <=0:
            flash("Nie podano żadnego typu zadań", "alert-danger")
            return redirect(url_for("startquiz"))
        if request.form.get("task_num") in ['0', None]:
            flash("Nie podano ilości pytań", "alert-danger")
            return redirect(url_for("startquiz"))
        
        #[random.randrange(mongo.db.tasks.count_documents({"atype": {"$in":types[:]}}))]
        
        taskmongo=mongo.db.tasks.aggregate([
            {"$match":{"atype": {"$in":types[:]}}},
            {"$sample":{"size": int(request.form.get('task_num'))}}
            ])
        
        tasks=[]

        for task in taskmongo:
            doc={"q":task['q'], 'task_id':str(task['_id'])}
            if task["atype"]=='abc':
                answers=[]
                count=0
                if len(task['answer'])<=2:
                    count=random.randint(1, len(task["answer"]))
                else:
                    count=random.randint(1, len(task['answer'])//2)
                temp=task["answer"][:]
                for _ in range(count):
                    x =random.randrange(len(temp))
                    answers.append(temp[x])
                    del temp[x]
                
                temp=task["mock"][:]

                while len(answers)<4 and len(temp)>0:
                    x =random.randrange(len(temp))
                    answers.append(temp[x])
                    del temp[x]

                random.shuffle(answers)
                doc["answers"]=answers
            tasks.append(doc)
                
        return render_template('quiz.html', tasks=tasks)
    
    count = mongo.db.tasks.count_documents({})
    enable=True
    if count==0:
        enable==False
        flash("W bazie danych nie ma żadnych zadań!", "alert-danger")

    return render_template("quiz-start.html", enable=enable, count=count)

@app.route("/quiz-results", methods=["POST", "GET"])
def quizresults():
    if request.method!='POST':
        return redirect(url_for("startquiz"))

    responses=json.loads(request.form['response'])
    
    results: list[dict] = []

    

    for resp in responses:
        task=mongo.db.tasks.find_one({"_id":ObjectId(resp['task_id'])}, {"_id":0})
        r={}
        if task['atype']=="command":
            command=resp['command']
            command=list(shlex.shlex(command, None, True, True))
            result=cmdparse.checkcmd(command, task["answer"])#[0]

            r['q']=task['q']
            r['user']=resp['command']
            r['result']=result
            r['answer']=[]
            for i in task["answer"]:
                r['answer'].append(cmdparse.cmd2str(i))

        elif task['atype']=='abc':
            r['q']=task['q']
            r['user']=resp['answer']
            result=False
            r['answer']=[]
            for i in task['answer']:
                r['answer'].append(i)
                if i==resp['answer']:
                    result=True
            r['result']=result
        results.append(r)

    return render_template('quiz-results.html', results=results, contact_mail=cfg['general'].get('contact_mail'))

@app.route('/admin')
def adminpanel():
    return render_template("admin/index.html")

@app.route('/resources')
def resourcespage():
    return render_template("resources.html")

errorquotes=[
    "Chyba pomyliłeś odwagę z odważnikiem, Panie Kolego!",
    "Masz predyspozycje do bycia strażakiem. Co prawda małe, ale zawsze jakieś!",
    "Jak nie ma progresu, to oznacza, że jest <i><b>regres</b></i>.",
    "Zawsze należy inwestować w najlepszy sprzęt.",
    "Te wkrętarki z firmy Dedra to takie średnie są."
]

@app.errorhandler(404)
def page_404(e):
    return render_template("404.html", quote=random.choice(errorquotes)), 404

@app.errorhandler(500)
def page_500(e):
    import datetime
    return render_template("err500.html", date=str(datetime.datetime.now()), quote=random.choice(errorquotes)), 500

if __name__=="__main__":
    app.run()