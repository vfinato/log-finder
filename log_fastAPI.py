import pyodbc
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
import os
import shutil
from datetime import datetime
from pathlib import Path

api_log_path = os.path.join(os.getcwd(), "/logs/api_calls/api_calls.log")
max_api_log_size = 10*1024*1024
LOGS_FOLDER = Path("C:/logs")

app = FastAPI()

def get_db_connection():
    """
    Return a connection to the SQL Server database.

    Returns:
        pyodc.Connection
    """
    conn = pyodc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=pythonAPI;"
        "DATABASE=Python;"
        "UID=pyUser;"
        "PWD=pyUserTestAPI@123"
    )
    return conn

api_key_header = APIKeyHeader(name="userKey")

def validate_userkey(userkey: str):
    """
    Validate a userkey with the database.

    Args:
        userkey (str): userkey to be validated

    Returns:
        str: username associated with the userkey

    Raises:
        HTTPException: 401 if the userkey is invalid
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT login FROM usersLogApi where userkey = ?", userkey)
    result = cursor.fetchall()

    if not result:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    username = result[0]
    conn.close()
    return username

def log_call(username: str, ip_address: str, endpoint:str, filename=""):
    """
    Write a log entry to the api_calls.log file.

    Args:
        username (str): username of the user who made the API call
        ip_address (str): IP address of the user who made the API call
        endpoint (str): endpoint which was accessed
        filename (str, optional): filename which was accessed. Defaults to ""
    """
    if os.path.exists(api_log_path):
       log_size = os.path.getsize(api_log_path)

       if log_size >= max_api_log_size:
           current_time = datetime.now().strftime("%Y%m%d%H%M%S")
           new_log_file = f"api_calls_{current_time}.log"
           shutil.move(api_log_path, new_log_file)


    with open(api_log_path, "a") as log_file:
        if filename != "":
            log_file.write(f"{datetime.now()} - User: {username} - IP: {ip_address} - Endpoint: {endpoint} - Filename: {filename}\n")
        else:
            log_file.write(f"{datetime.now()} - User: {username} - IP: {ip_address} - Endpoint: {endpoint}\n")



@app.get("/logs")
async def list_logs(request: Request, userkey: str = Depends(api_key_header)):
    """
    List all available logs in the LOGS_FOLDER directory.

    Args:
        request (Request): The request object
        userkey (str): The userkey to be validated

    Returns:
        dict: A dictionary containing the list of log files with the key 'logs'

    Raises:
        HTTPException: 401 if the userkey is invalid
        HTTPException: 404 if no log files are found
    """
    #username = validate_userkey(userkey)

    client_ip = request.client.host
    log_call(userkey, client_ip, "List Logs")

    log_files = [f.name for f in LOGS_FOLDER.glob("*.log")]

    if not log_files:
        raise HTTPException(status_code=404, detail="Nenhum log Encontrado")

    return {"logs": log_files}

@app.get("/logs/{filename}")
async def read_log(request: Request, filename: str, userkey: str = Depends(api_key_header)):
    """
    Read the content of a log file.

    Args:
        request (Request): The request object
        filename (str): The name of the log file to be read
        userkey (str): The userkey to be validated

    Returns:
        dict: A dictionary with the log file name and its content

    Raises:
        HTTPException: 401 if the userkey is invalid
        HTTPException: 404 if the log file is not found
    """
    #username = validate_userkey(userkey)
    log_path = LOGS_FOLDER / filename

    client_ip = request.client.host
    log_call(userkey, client_ip, "Read Log", filename)

    if not log_path.is_file():
        raise HTTPException(status_code=404, detail="Log não encontrado")

    with open(log_path, "r") as f:
        log_content = f.read()

    return {"file": filename, "content": log_content}

@app.get("/logs/download/{filename}")
async def download_log(request: Request, filename: str):
    """
    Download a log file.

    Args:
        request (Request): The request object
        filename (str): The name of the log file to be downloaded

    Returns:
        FileResponse: A FileResponse object containing the log file

    Raises:
        HTTPException: 401 if the userkey is invalid
        HTTPException: 404 if the log file is not found
    """
   # username = validate_userkey(userkey)
    log_path = LOGS_FOLDER / filename

    client_ip = request.client.host
    log_call("vitor", client_ip, "Download Log", filename)

    if not log_path.is_file():
        raise HTTPException(status_code=404, detail="Log não encontrado")

    return FileResponse(log_path, media_type="application/octet-stream", filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)