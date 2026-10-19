# <span style="color:#211a52">AAU Bachelor - Secure Messaging System</span>

This repository contains the code for a secure messaging system developed as a bachelor's project at Aalborg University (AAU). The project focuses on creating a backend for secure communication, with emphasis on authentication, secure message handling, and API-based communication. It is designed as a practical software engineering project that explores how a secure messaging system can be implemented and evaluated in a real-world setting.

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
