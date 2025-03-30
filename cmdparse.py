def checkcmd(command:list[str], answers:list[dict])-> bool:
    result=False
    if len(command)!=0:
        for answer in answers:
            c=command[1:]
            if command[0].lower()!=answer["command"].lower():
                if command[0].lower()=='sudo' and command[1].lower()==answer["command"].lower():
                    c=c[1:]
                else:
                    continue
            if answer["type"]=='posix':
                options={"short":[], 'long':[]}
                params: list[dict]=[]
                texts=[]
                last_option=None
                accept_options=True
                for arg in c:
                    if arg == '--':
                        accept_options=False
                    elif arg.startswith('--') and accept_options:
                        options["long"].append(arg[2:].lower())
                        last_option=(arg[2:].lower(), 'long')
                    elif arg.startswith('-') and len(arg)>1 and accept_options:
                        for i in arg[1:]:
                            options["short"].append(i)
                            last_option=(i, 'short')
                    else:
                        texts.append(arg.lower())
                        if last_option!=None:
                            if last_option[1]=='short':
                                params.append({'shname':last_option[0], 'value':arg.lower()})
                            else:
                                params.append({'name':last_option[0].lower(), 'value':arg.lower()})
                            last_option=None

                argnum=len(answer['args']) #counts if all of the args in the (correct) answer were fulfiled

                for arg in answer["args"]:
                    if arg['argtype']=='option':
                        if arg['name'].lower() in options['long'] or arg.get('shname') in options["short"]:
                            argnum-=1
                            try:
                                if 'shname' in arg.keys():
                                    options["short"].remove(arg['shname'])
                                options['long'].remove(arg['name'].lower())
                            except ValueError:
                                pass
                            for i in range(len(params)):
                                if params[i].get('shname')==arg.get("shname") or params[i].get('name')==arg["name"].lower():
                                    del params[i]
                                    break

                    elif arg['argtype']=='param':
                        for i in range(len(params)):
                            if (params[i].get('shname')==arg.get("shname") or params[i].get('name')==arg["name"].lower()) and params[i]['value']==arg["value"].lower():
                                argnum-=1
                                del params[i]
                                try:
                                    if 'shname' in arg.keys():
                                        options["short"].remove(arg['shname'])
                                    options['long'].remove(arg['name'].lower())
                                except ValueError:
                                    pass
                                if arg['value'].lower() in texts:
                                    texts.remove(arg['value'].lower())
                                break

                    elif arg['argtype']=='text':
                        if arg['value'].lower() in texts:
                            argnum-=1
                            texts.remove(arg['value'].lower())
                            for i in range(len(params)):
                                if params[i]['value']==arg["value"].lower():
                                    del params[i]
                                    break
                if argnum==0 and len(options["long"])==0 and len(options['short'])==0 and len(texts)==0 and len(params)==0:
                    result=True
                    break
            elif answer['type']=='dd':
                params ={}
                for arg in c:
                    div=arg.find("=")
                    if div==-1:
                        return False # dd doesn't allow textual arguments
                    params[arg[:div].lower()]=arg[div+1:]

                argnum=len(answer['args']) #counts if all of the args in the (correct) answer were fulfiled

                for opt, value in answer["args"].items():
                    if params.get(opt.lower()).lower() == value.lower():
                        argnum-=1
                        del params[opt.lower()]
                    
                if argnum==0 and len(params)==0:
                    result=True
                    break
    return (result)

def cmd2str(command: dict, multi=False) -> str:
    ret=''
    string: list[str]=[]
    if multi:
        pass #TODO: multi commands
    else:
        if command['type']=='posix':
            string.append(command['command'])
            flagbuff=''
            for arg in command["args"]:

                if (arg["argtype"] not in ['option', 'param'] or arg.get("shname") == None) and len(flagbuff)!=0:
                    string.append(f"-{flagbuff}")
                    flagbuff=''

                if arg['argtype'] in ['text']:
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

            f=True
            for i in string:
                
                if ' ' in i or '"' in i:
                    i= "'"+i.replace("'", "'\"'\"'")+"'"
                else:
                    i=i.replace("'", "\"'\"")
                ret+=('' if f else ' ')+i
                f=False
        elif command['type']=='dd':
            ret+=command['command']
            for opt, value in command["args"].items():
                if ' ' in value or '"' in value:
                    value = "'"+value.replace("'", "'\"'\"'")+"'"
                else:
                    value=value.replace("'", "\"'\"")
                ret+=f' {opt}={value}'

    return ret

