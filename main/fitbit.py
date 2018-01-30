from urllib import urlencode
from urlparse import urlparse
import BaseHTTPServer
from multiprocessing import Process, freeze_support
import webbrowser
import requests
import json
import os
import datetime
import db_ops

'''
The Flow:
- make a call
    - access token exists
        - make call
            - if fails with expired
                - get new token using refresh token
                - if fails
                    - do auth
    - access token doesnt exist
        - check auth code exists
            - get new access token
        - auth code doesnt exist
            - do auth
'''

secrets_dir = "."
secret_file = os.path.join(secrets_dir, "fitbit_secret.json")
authorization_file = os.path.join(secrets_dir, "auth_file")
access_token_file = os.path.join(secrets_dir, "access_file.json")
secrets = {}

def load_secrets():
    global secrets
    with open(secret_file) as f:
        secrets = json.loads(f.read())

def get_secret(secret):
    if len(secrets) == 0:
        load_secrets()
    return secrets.get(secret, None)

def parse_n_save_auth_code(url_path):
    query = urlparse(url_path).query
    auth_code = query.replace("code=", "")
    with open(authorization_file, 'w') as f:
        f.write(auth_code)

def start_server():
    class MyHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            parse_n_save_auth_code(self.path)
            self.wfile.write("Successfully authorized.")
            self.wfile.flush()

    server_address = ('', 8080)
    httpd = BaseHTTPServer.HTTPServer(server_address, MyHTTPRequestHandler)
    httpd.handle_request()

def start_server_wrapper():
    p = Process(target=start_server)
    p.start()
    return p

def do_auth():
    base_url = "https://www.fitbit.com/oauth2/authorize"
    params = {
        "client_id": get_secret("client_id"),
        "response_type": "code",
        "scope": "activity"
    }
    url = base_url + "?" + urlencode(params)

    server_proc = start_server_wrapper()

    webbrowser.open(url)
    # save token

    # waiting for user action to finish
    server_proc.join()

def is_access_code_valid(token):
    url = "https://api.fitbit.com/oauth2/introspect"
    data = {
        "token": token
    }
    headers = {
        "Authorization": "Bearer " + token
    }
    resp = requests.post(url, headers=headers, data=data)
    # print resp.text
    return json.loads(resp.text).get("active", 0) > 0

def get_access_token():
    access_token = None
    if not os.path.isfile(access_token_file):
        print "getting new access token"
        access_token = get_new_access_token()
    else:
        with open(access_token_file) as f:
            tk = json.loads(f.read())
        access_token = tk["access_token"]
        if not is_access_code_valid(access_token):
            print "have to refresh access token"
            access_token = refresh_access_token(tk["refresh_token"])
        else:
            print "using access token from file"
    return access_token

def del_file(filename):
    try:
        os.remove(filename)
    except OSError as oer:
        None

def del_files():
    del_file(authorization_file)
    del_file(access_token_file)

def refresh_access_token(refresh_token):
    return get_new_access_token(refresh_token)

def get_new_access_token(refresh_token = None):
    client_id = get_secret("client_id")
    client_secret = get_secret("client_secret")

    data = {
        "client_id": get_secret("client_id"),
        "expires_in": 3600 # in seconds
    }

    # for new token need to use auth code
    # for refresh need to use refresh_token
    if refresh_token:
        data["refresh_token"] = refresh_token
        data["grant_type"] = "refresh_token"
    else:
        if not os.path.isfile(authorization_file):
            do_auth()
        with open(authorization_file) as f:
            auth_code = f.read()

        data["code"] = auth_code
        data["grant_type"] = "authorization_code"

    url = "https://api.fitbit.com/oauth2/token"
    response = requests.post(url, auth=(client_id, client_secret), data=data)
    resp_json = json.loads(response.text)
    status_code= response.status_code
    if status_code == 200:
        with open(access_token_file, 'w') as f:
            f.write(json.dumps(resp_json, indent = 2))
        return resp_json["access_token"]
    else:
        print "error getting access token"
        print "error code:", status_code
        print json.dumps(resp_json["errors"], indent = 2)
        del_files()
        print "try again"
        return None

def get_date_range():
    # strftime("%Y-%m-%d") or .isoformat()
    start_date = db_ops.get_last_activity_date()
    if start_date:
        start_date += datetime.timedelta(days=1)
    else:
        # getting almost all the data
        start_date = datetime.date(2017, 3, 1)
        start_date = start_date - datetime.timedelta(days=start_date.isocalendar()[2]-1)

    end_date = datetime.date.today() - datetime.timedelta(days=1)
    return (start_date, end_date)

def fetch_data(start_date, end_date):
    url = "https://api.fitbit.com/1/user/-/activities/steps/date/<base-date>/<end-date>.json"
    url = url.replace("<base-date>", start_date)
    url = url.replace("<end-date>", end_date)
    print url

    access_token = get_access_token()
    headers = {
        "Authorization": "Bearer " + access_token
    }
    resp = requests.get(url, headers=headers)
    # print resp.status_code
    print json.dumps(json.loads(resp.text), indent = 2)
    return json.loads(resp.text)

def fetch_n_save_new_data():
    start_date, end_date = get_date_range()

    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()

    # there has to be at least 1 days time difference
    if end_date - start_date >= datetime.timedelta(days=0):
        print "fetching date from {} to {}".format(start_date_str, end_date_str)
    else:
        print "found invalid date range: {} to {}".format(start_date_str, end_date_str)
        return

    # print start_date, end_date
    data = fetch_data(start_date_str, end_date_str)
    db_ops.save_data(data)

if __name__ == "__main__":
    freeze_support() # needed for windows

    print get_date_range()
    # fetch_n_save_new_data()
    # fetch_data(datetime.date(2018, 1, 20).isoformat(), datetime.date(2018, 1, 25).isoformat())
