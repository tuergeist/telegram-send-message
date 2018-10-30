import cherrypy
import os
import psycopg2
import requests
import _thread, time
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('html'))

DATABASE_URL = os.environ['DATABASE_URL']
TELEGRAM_BOT = os.environ['TELEGRAM_BOT']
CALLBACK_URL = os.environ['CALLBACK_URL']

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id integer PRIMARY KEY,
    username text
)
""")
conn.commit()


def telegram_request(endpoint, params=None):
    url = 'https://api.telegram.org/' + TELEGRAM_BOT + '/' + endpoint
    r = requests.get(url, params=params)
    return r


def get_updates():
    count = 0
    while count < 100:
        time.sleep(5)
        count += 1
        r = telegram_request('getUpdates')
        print(r.status_code, r.headers['content-type'], r.encoding)
        print(r.text)
        print(r.json())
        print(count)


class MessageSender(object):
    @cherrypy.expose
    def index(self):
        data_to_show = ['Hello', 'world']
        tmpl = env.get_template('index.html')
        return tmpl.render(data=data_to_show)

    @cherrypy.expose
    def test(self):
        r = telegram_request('getWebhookinfo')
        print(r.text)

    @cherrypy.expose
    def send(self, user_id, message):
        if message is None:
            raise cherrypy.HTTPError(400, message="need a message as parameter")
        r = telegram_request('sendMessage', {'chat_id': user_id, 'text': message})
        print(r.text)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def callback(self):
        data = cherrypy.request.json
        print('CALLBACK')
        print(data)

        text = data['message']['text']
        if text == '/list':
            try:
                query = """SELECT * FROM  users"""
                cur.execute(query)
                for r in cur:
                    print(r)
            except Exception as e:
                print('Error ', e)
        if text == '/subscribe':
            try:
                user_id = data['message']['from']['id']
                user_name = data['message']['from']['first_name'] + ' ' + data['message']['from']['last_name']
                query = """
                    INSERT INTO users (id, username) VALUES ({}, '{}')
                """.format(user_id, user_name)
                #print(query)
                cur.execute(query)
                conn.commit()
            except Exception as e:
                print('Error ', e)
            self.send(user_id, "Welcome " + user_name)

config = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(os.environ.get('PORT', 5000)),
    },
    '/assets': {
        'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
        'tools.staticdir.on': True,
        'tools.staticdir.dir': 'assets',
    }
}


def start_thread():
    try:
       _thread.start_new_thread( get_updates, () )
    except:
       print("Error: unable to start thread")


def _register_webhook():
    time.sleep(15)
    url = 'https://api.telegram.org/' + TELEGRAM_BOT + '/setWebhook'
    r= requests.get(url,  data={'url': CALLBACK_URL})
    print(r.status_code, r.headers['content-type'], r.encoding)
    print(r.text)


def register_webhook():
    _thread.start_new_thread(_register_webhook, ())

register_webhook()
#start_thread
cherrypy.quickstart(MessageSender(), config=config)
