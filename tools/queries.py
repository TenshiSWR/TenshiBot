from dotenv import load_dotenv
from json import loads
from os import getenv
import requests
from requests_oauthlib import OAuth1
from tools.misc import QueryError

load_dotenv()
USER_AGENT = loads(getenv("USER-AGENT"))
OAUTH_KEY = loads(getenv("OAUTH"))
_AUTH = OAuth1(OAUTH_KEY[0], OAUTH_KEY[1], OAUTH_KEY[2], OAUTH_KEY[3])
del OAUTH_KEY

# Important note: Local account must exist on the wiki in order to use OAuth and the API.


def get_lint_errors(lint_type: str or bool = None, namespaces: str or bool = None, url: str = "https://en.wikipedia.org") -> list:
    if type(lint_type) is str:
        lint_type.replace("+", "%7C")
    if type(namespaces) is str:
        lint_type.replace("+", "%7C")
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
    while True:
        if lntfrom:
            r = requests.get(api_query+"&lntfrom={}".format(lntfrom), auth=_AUTH, headers=USER_AGENT)
        else:
            r = requests.get(api_query, auth=_AUTH, headers=USER_AGENT)
        decoded = loads(r.text)
        full_list += decoded["query"]["linterrors"]
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


