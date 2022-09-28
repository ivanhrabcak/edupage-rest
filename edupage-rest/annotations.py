from dataclasses import asdict, is_dataclass
from functools import wraps
from fastapi import HTTPException

from .edupage import get_edupage

def returns_edupage_object(method):
    @wraps(method)
    def __impl(*method_args, **method_kwargs):
        output = method(*method_args, **method_kwargs)

        if is_dataclass(output):
            return asdict(output)
        elif isinstance(output, list):
            if len(output) != 0:
                return [asdict(x) if is_dataclass(x) else x for x in output]
            else:
                return []
        else:
            return output
    
    return __impl

def logged_in(method):
    @wraps(method)
    def __impl(*method_args, **method_kwargs):
        if not get_edupage().is_logged_in:
            raise HTTPException(status_code=400, detail="You first have to log in!")

        return method(*method_args, **method_kwargs)
    
    return __impl


        