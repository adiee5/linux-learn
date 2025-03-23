from flask import Flask, render_template, request, abort, redirect, url_for, flash
import json, shlex, configparser, random
from flask_pymongo import PyMongo
from bson import ObjectId

app = Flask(__name__)

cfg = configparser.ConfigParser()

cfg.read('server.ini')

app.config['SECRET_KEY'] = cfg['general']['SECRET_KEY']
app.config["MONGO_URI"] = f"mongodb://{cfg['mongodb'].get('ip', 'localhost')}:{cfg['mongodb'].get('port','27017')}/{cfg['mongodb']['db']}"

mongo= PyMongo(app)

app.app_context().push()



@app.route('/quiz', methods=["POST", "GET"])
def startquiz():
    if request.method == 'POST':
        types=request.form.getlist('filters')

        if len(types) <=0:
            flash("Nie podano żadnego typu zadań", "alert-danger")
            return redirect(url_for("startquiz"))
        
        task=mongo.db.tasks.find({"atype": {"$in":types[:]}})[random.randrange(mongo.db.tasks.count_documents({"atype": {"$in":types[:]}}))]

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
    
    return render_template("quiz-start.html")


@app.route("/quiz-results", methods=["POST", "GET"])
def quizresults():
    if request.method!='POST':
        return redirect(url_for("startquiz"))

    task=mongo.db.tasks.find_one({"_id":ObjectId(request.form['task_id'])}, {"_id":0})
    command=request.form['command'].strip()
    command=shlex.split(command)
    result=False
    if len(command)!=0:
        for answer in task["answer"]:
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

    return render_template('quiz-results.html', question=json.dumps(task), command=request.form['command'].strip(), zdane=result, debug=command)

@app.route('/resources')
def resourcespage():
    return render_template("resources.html")

@app.errorhandler(404)
def page_404(e):
    return render_template("404.html"), 404

if __name__=="__main__":
    app.run()