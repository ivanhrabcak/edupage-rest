from edupage_api import Edupage

# global access to an edupage instance
def get_edupage(edupage = Edupage()):
    return edupage