from flask import Flask, render_template, request, abort, redirect, url_for, flash
import json, shlex, configparser, random
from flask_pymongo import PyMongo
from bson import ObjectId

app = Flask(__name__)

cfg = configparser.ConfigParser()

cfg.read('server.ini')

app.config['SECRET_KEY'] = cfg['general']['SECRET_KEY']

if cfg['mongodb'].get('url')!=None:
    app.config["MONGO_URI"] = cfg['mongodb']['url']
else:
    app.config["MONGO_URI"] = "mongodb://"+ (f"{cfg['mongodb'].get('login')}:{cfg['mongodb'].get('password')}@" if cfg['mongodb'].get('login')!=None or cfg['mongodb'].get('password')!=None else '') + f"{cfg['mongodb'].get('ip', 'localhost')}:{cfg['mongodb'].get('port','27017')}/{cfg['mongodb']['db']}"

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
        
        task=list(mongo.db.tasks.aggregate([
            {"$match":{"atype": {"$in":types[:]}}},
            {"$sample":{"size": 1}}
            ]))[0]

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
            return render_template('quiz.html', question=task['q'], task_id=str(task['_id']), answers=answers)

        return render_template('quiz.html', question=task['q'], task_id=str(task['_id']))
    
    count = mongo.db.tasks.count_documents({})
    enable=True
    if count==0:
        enable==False
        flash("W bazie danych nie ma żadnych zadań!", "alert-danger")

    return render_template("quiz-start.html", enable=enable, count=count)

def checkcmd(command:list[str], answers:list[dict])-> tuple[bool]:
    result=False
    if len(command)!=0:
        for answer in answers:
            c=command[1:]
            if command[0]!=answer["command"]:
                if command[0]=='sudo' and command[1]==answer["command"]:
                    c=c[1:]
                else:
                    continue
            options={"short":[], 'long':[]}
            params: list[dict]=[]
            texts=[]
            last_option=None
            accept_options=True
            for arg in c:
                if arg == '--':
                    accept_options=False
                elif arg.startswith('--') and accept_options:
                    options["long"].append(arg[2:])
                    last_option=(arg[2:], 'long')
                elif arg.startswith('-') and len(arg)>1 and accept_options:
                    for i in arg[1:]:
                        options["short"].append(i)
                        last_option=(i, 'short')
                else:
                    texts.append(arg)
                    if last_option!=None:
                        if last_option[1]=='short':
                            params.append({'shname':last_option[0], 'value':arg})
                        else:
                            params.append({'name':last_option[0], 'value':arg})
                        last_option=None

            argnum=len(answer['args']) #counts if all of the args in the (correct) answer were fulfiled

            for arg in answer["args"]:
                if arg['argtype']=='option':
                    if arg['name'] in options['long'] or arg.get('shname') in options["short"]:
                        argnum-=1
                        try:
                            if 'shname' in arg.keys():
                                options["short"].remove(arg['shname'])
                            options['long'].remove(arg['name'])
                        except ValueError:
                            pass
                        for i in range(len(params)):
                            if params[i].get('shname')==arg.get("shname") or params[i].get('name')==arg["name"]:
                                del params[i]
                                break

                elif arg['argtype']=='param':
                    for i in range(len(params)):
                        if (params[i].get('shname')==arg.get("shname") or params[i].get('name')==arg["name"]) and params[i]['value']==arg["value"]:
                            argnum-=1
                            del params[i]
                            try:
                                if 'shname' in arg.keys():
                                    options["short"].remove(arg['shname'])
                                options['long'].remove(arg['name'])
                            except ValueError:
                                pass
                            if arg['value'] in texts:
                                texts.remove(arg['value'])
                            break

                elif arg['argtype']=='text':
                    if arg['value'] in texts:
                        argnum-=1
                        texts.remove(arg['value'])
                        for i in range(len(params)):
                            if params[i]['value']==arg["value"]:
                                del params[i]
                                break
            if argnum==0 and len(options["long"])==0 and len(options['short'])==0 and len(texts)==0 and len(params)==0:
                result=True
                break
    return (result)

def cmd2str(command: dict, multi=False) -> str:
    string: list[str]=[]
    if multi:
        pass #TODO: multi commands
    else:
        string.append(command['command'])
        flagbuff=''
        for arg in command["args"]:

            if (arg["argtype"] not in ['option', 'param'] or arg.get("shname") == None) and len(flagbuff)!=0:
                string.append(f"-{flagbuff}")
                flagbuff=''

            if arg['argtype'] in ['text', 'file']:
                string.append(arg["value"])

            if arg["argtype"]=='option':
                if arg.get("shname")!=None:
                    flagbuff+=arg["shname"]
                else:
                    string.append(f"--{arg['name']}")

            if arg["argtype"]=='param':
                if arg.get("shname")!=None:
                    flagbuff+=arg["shname"]
                    string.append(f"-{flagbuff}")
                    flagbuff=''
                else:
                    string.append(f"--{arg['name']}")
                string.append(arg['value'])

        if len(flagbuff)!=0:
            string.append(f"-{flagbuff}")

    ret=''
    for i in string:
        
        if ' ' in i or '"' in i:
            i= "'"+i.replace("'", "'\"'\"'")+"'"
        else:
            i.replace("'", "\"'\"")
        ret+=' '+i
    return ret



@app.route("/quiz-results", methods=["POST", "GET"])
def quizresults():
    if request.method!='POST':
        return redirect(url_for("startquiz"))
    
    results: list[dict] = []

    results.append({})
    command=None

    task=mongo.db.tasks.find_one({"_id":ObjectId(request.form['task_id'])}, {"_id":0})
    if task['atype']=="command":
        command=request.form['command'].strip()
        command=list(shlex.shlex(command, None, True, True))
        result=checkcmd(command, task["answer"])#[0]

        results[0]['q']=task['q']
        results[0]['user']=request.form['command'].strip()
        results[0]['result']=result
        results[0]['answer']=[]
        for i in task["answer"]:
            results[0]['answer'].append(cmd2str(i))

    elif task['atype']=='abc':
        results[0]['q']=task['q']
        results[0]['user']=request.form['answer']
        result=False
        results[0]['answer']=[]
        for i in task['answer']:
            results[0]['answer'].append(i)
            if i==request.form['answer']:
                result=True
        results[0]['result']=result

    return render_template('quiz-results.html', results=results, debug=command)


@app.route('/resources')
def resourcespage():
    return render_template("resources.html")

errorquotes=[
    "Chyba pomyliłeś odwagę z odważnikiem, Panie Kolego!",
    "Masz predyspozycje do bycia strażakiem. Co prawda małe, ale zawsze jakieś!",
    "Jak nie ma progresu, to oznacza, że jest <i><b>regres</b></i>."
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