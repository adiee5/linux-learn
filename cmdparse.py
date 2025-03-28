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

    ret=''
    f=True
    for i in string:
        
        if ' ' in i or '"' in i:
            i= "'"+i.replace("'", "'\"'\"'")+"'"
        else:
            i.replace("'", "\"'\"")
        ret+=('' if f else ' ')+i
        f=False
    return ret

