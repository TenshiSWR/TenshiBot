from dotenv import load_dotenv
from json import loads
from os import getenv
import requests
from requests_oauthlib import OAuth1
from tqdm import tqdm
from tools.misc import QueryError

load_dotenv()
USER_AGENT = loads(getenv("USER-AGENT"))
OAUTH_KEY = loads(getenv("OAUTH"))
_AUTH = OAuth1(OAUTH_KEY[0], OAUTH_KEY[1], OAUTH_KEY[2], OAUTH_KEY[3])
S = requests.Session()
S.auth, S.headers = _AUTH, USER_AGENT
del OAUTH_KEY

# Important note: Local account must exist on the wiki in order to use OAuth and the API.


def get_lint_errors(lint_type: str | bool = None, namespaces: str | bool = None, url: str = "https://en.wikipedia.org") -> list:
    if type(lint_type) is str:
        lint_type.replace("+", "%7C")
    if type(namespaces) is str:
        lint_type.replace("+", "%7C")
    data = loads(S.get(url+"/w/api.php?action=query&format=json&meta=linterstats&formatversion=2").text)
    total = 0
    for lint_error in lint_type.split("%7C"):
        total += data["query"]["linterstats"]["totals"][lint_error]
    divisor = total / 320  # Purely guessing, I don't know if there's a ratio or some other total I'm missing
    max = int((total // (500+divisor))+2)  # And there's some weird fluctuation that happens sometimes
    if lint_type and not namespaces:
        api_query = f"{url}/w/api.php?action=query&format=json&prop=&list=linterrors&formatversion=2&lntcategories={lint_type}&lntlimit=500"
    elif not lint_type and namespaces:
        api_query = f"{url}/w/api.php?action=query&format=json&prop=&list=linterrors&formatversion=2&lntlimit=500&lntnamespace={namespaces}"
    elif not lint_type and not namespaces:
        api_query = f"{url}/w/api.php?action=query&format=json&prop=&list=linterrors&formatversion=2&lntlimit=500"
    else:
        api_query = f"{url}/w/api.php?action=query&format=json&prop=&list=linterrors&formatversion=2&lntcategories={lint_type}&lntlimit=500&lntnamespace={namespaces}"
    full_list = []

    lntfrom = None
    bar = tqdm(desc=url+" Lint errors", total=max*500)
    while True:
        bar.update(500)
        if lntfrom:
            r = S.get(api_query+"&lntfrom={}".format(lntfrom))
        else:
        decoded = loads(r.text)
        full_list += decoded["query"]["linterrors"]
            r = S.get(api_query)
        try:
            decoded["warnings"]
        except KeyError:
            pass
        else:
            raise QueryError(decoded["warnings"]["linterrors"]["warnings"])
        try:
            lntfrom = decoded["continue"]["lntfrom"]
        except KeyError:
            break
    return full_list


