import re
import os
import json
from decouple import Config, RepositoryEnv, UndefinedValueError
from redis import StrictRedis

room_to_chatbot_user = {
    # Contains a mapping from the room names to the Chatbot Users
    # We need to populate this from the User DB, but for now, we'll put some sample values
    'lobby': 'Susan',
    'default': 'Gerald',
}

DOTENV_FILE = os.path.join(os.getcwd(), 'livechat', '.env')
env_config = Config(RepositoryEnv(DOTENV_FILE))

HOST = env_config.get('REDIS_SERVER_HOST')
try:
    PASSWORD = env_config.get('REDIS_SERVER_PASSWORD')
except UndefinedValueError:
    PASSWORD = None
PORT = env_config.get('REDIS_SERVER_PORT')

class ChatBotUser():
    def __init__(self, chatbot_user, template):
        self.name = chatbot_user
        self.content, self.hashmap = self.process_template(template)
        self.state = 1
        if PASSWORD == None:
            self.redis_connection = StrictRedis(host=HOST, port=PORT)
        else:
            self.redis_connection = StrictRedis(host=HOST, password=PASSWORD, port=PORT)
    
    def process_template(self, template_json):
        # We'll process the template JSON and put it into a Database
        file_obj = open(template_json, 'rb')
        content = json.load(file_obj)
        file_obj.close()

        # Create a hashmap to sequentially order the id's
        hashmap = dict()
        curr = 1
        for node in content['node']:
            if 'id' in node:
                hashmap[node['id']] = curr
                curr += 1
        return content, hashmap
    

    def insert_placeholders(self, message, has_options):
        # Hello {username} => Hello {redis_connection.get('username')}
        pattern = r"\{([A-Za-z0-9_]+)\}"
        encoding = 'utf-8'
        def replace_function(match):
            # Strip away the '{' and '}' from the match string
            match = match.group()[1:-1]
            # Redis gives us a byte string. Decode that to 'utf-8' and convert to a string
            return str(self.redis_connection.get(match).decode(encoding))
        message = re.sub(pattern, replace_function, message)
        if has_options is True:
            message += '\n'
            for idx, option in enumerate(self.options):
                message += str(idx) + '. ' + option + '\n'
        return message


    def process_message(self, message, initial_state, user):
        self.state = initial_state
        
        print(f"At state {self.state}, received {message}")
        
        node = self.content['node'][initial_state - 1]
        
        self.has_options = False

        # The type of the reply from the Chatbot (text, button, etc)
        self.msg_type = None

        if 'store' in node:
            key = node['store']
            self.redis_connection.set(key, message)

        if 'options' in node:
            self.has_options = True

        msg = None

        if 'message' in node:
            msg = self.insert_placeholders(node['message'], self.has_options)

        if 'options' in node:
            self.options = node['options']
            if 'message' in node:
                msg += '\n'
            else:
                msg = ""
            for idx, option in enumerate(node['options']):
                msg += str(idx) + ". " + option + "\n"

        if 'user' in node:
            # Wait for user input
            print(f"Current user {user}")
            if 'AnonymousUser' in str(user):
                return None, self.state, None
            else:
                print('Received user input!')
                if self.has_options is True:
                    for idx, option in enumerate(node['options']):
                        if option == message:
                            print(f"Selected option {option}!")
                            if isinstance(node['trigger'], list):
                                next_state = self.hashmap[node['trigger'][idx]]
                            else:
                                next_state = self.hashmap[node['trigger']]
                            self.state = next_state
                            print(f"next_state = {next_state}")

        if 'end' in node:
            # Last State
            self.state = -1
            return self.insert_placeholders(node['message'], self.has_options), self.state, self.msg_type
        
        if 'trigger' in node:
            if isinstance(node['trigger'], list):
                pass
            else:
                next_state = self.hashmap[node['trigger']]
            try:
                # Check if the next node needs user input
                next_node = self.content['node'][next_state - 1]
                if 'user' in next_node:
                    if 'message' in next_node:
                        msg += '\n' + next_node['message']
                    if 'options' in next_node:
                        for idx, option in enumerate(next_node['options']):
                            msg += '\n' + str(idx) + '. ' + option
                    if 'type' in next_node:
                        self.msg_type = next_node['type']
                        #msg += '\n' + 'Type: ' + next_node['type']
            except IndexError:
                pass
            if 'message' in node:
                return msg, next_state, self.msg_type
            else:
                return self.process_message(msg, next_state, user), next_state, self.msg_type
        else:
            pass