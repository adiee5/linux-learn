import pathlib


# Yes, I know, I could've used an external library, but I didn't want to add additional pip dependencies for such insignificant thing and also the GitPython library is not server-safe, apparently.
getgit_cache=None
def getgit():
 
    if globals()["getgit_cache"]!=None:
        return getgit_cache
    
    HEAD= pathlib.Path('.','.git','HEAD')
    try:
        HEAD=open(HEAD).readline()
    except FileNotFoundError:
        getgit_cache=False
        return False
    if HEAD[:4]=='ref:':
        s=HEAD[4:].strip().split('/')
        try:
            getgit_cache=open(pathlib.Path('.','.git',*s)).readline().strip()
            return getgit_cache
        except FileNotFoundError:
            getgit_cache=False
            return False
    getgit_cache=HEAD
    return HEAD