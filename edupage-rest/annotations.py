from dataclasses import asdict, is_dataclass
from datetime import timedelta, datetime
from functools import wraps
import inspect
from types import FunctionType
from fastapi import HTTPException, Header
from cachetools import TTLCache

from edupage_api import Edupage

def get_global_ttl_cache(cache = TTLCache(maxsize=2000, ttl=timedelta(hours=2), timer=datetime.now)):
    return cache

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
        if not method_kwargs.get("token"):
            raise HTTPException(status_code=400, detail="No token specified!")
        
        token = method_kwargs["token"]

        cache = get_global_ttl_cache()       
        if not cache.get(token):
            raise HTTPException(status_code=400, detail="Invalid token!")
        
        if not cache[token].is_logged_in:
            raise HTTPException(status_code=400, detail="You first have to log in!")

        return method(*method_args, **method_kwargs)
    
    return __impl

def authenticated(method):
    def get_edupage_param_name(function):
        method_params = inspect.signature(function).parameters

        for param_name, parameter in method_params.items():
            if parameter.annotation == Edupage:
                return param_name
        
        return None
    
    edupage_param_name = get_edupage_param_name(method)
    
    def __impl(token: str | None = Header(default=None), *method_args, **method_kwargs):
        if not token:
            raise HTTPException(status_code=400, detail="No token specified!")
        
        cache = get_global_ttl_cache()

        cached_edupage = cache.get(token)
        if not cached_edupage:
            raise HTTPException(status_code=400, detail="Invalid token!")
        
        if edupage_param_name:
            method_kwargs[edupage_param_name] = cached_edupage
        
        return method(*method_args, **method_kwargs)
    
    param_name = get_edupage_param_name(method)
    if param_name:
        __impl.__signature__ = inspect.Signature(
            [
                *filter(lambda p: p.name != param_name, inspect.signature(method).parameters.values()),
                *filter(lambda p: p.kind not in [inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD], inspect.signature(__impl).parameters.values()),
            ],
            return_annotation=inspect.signature(method).return_annotation
        )

    return __impl

        