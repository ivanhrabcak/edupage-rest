# edupage-rest
This is a starting point for creating a small API that allows you to get data from edupage.

# Run
```shell
$ pip install -r requirements.txt
$ uvicorn edupage-rest.main:app
```

You can access the API documentation (swagger) by starting the API and going to `http://localhost:8000/docs`.

# Warning
This is far from production ready, it is only a starting point. It uses a global edupage object, so once someone logs in, everyone else using this API can access their account.

It should be pretty use to edit my code to add authentication and switch the account based on who's logged in.

Checkout FastAPI: https://fastapi.tiangolo.com/

# Issues
If you experience any issues or find any bugs, [feel free to open an issue](https://github.com/ivanhrabcak/edupage-rest/issues/new).