# <span style="color:#211a52">AAU Bachelor - Secure Messaging System</span>
### Backend

1. Navigate to the backend folder:

```bash
cd backend
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

```bash
source venv/bin/activate
```

4. Install the necessary packages in the virtual environment:

```bash
pip install -r requirements.txt
```

5. Start the backend:

```bash
fastapi dev main.py
```
or
```
uvicorn main:app --reload
```

6. Access the backend documentation at:

[http://localhost:8000/docs](http://localhost:8000/docs)

or 

[https://api.smaas.dk/docs](https://api.smaas.dk/docs)
