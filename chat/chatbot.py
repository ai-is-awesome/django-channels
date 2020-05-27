import json

room_to_chatbot_user = {
    # Contains a mapping from the room names to the Chatbot Users
    # We need to populate this from the User DB, but for now, we'll put some sample values
    'lobby': 'Susan',
    'default': 'Gerald',
}

class ChatBotUser():
    def __init__(self, chatbot_user, template):
        self.name = chatbot_user
        self.commands = self.process_template(template)
    
    
    def process_template(self, template_json):
        # We'll process the template JSON and put it into a Database
        file_obj = open(template_json, 'rb')
        content = file_obj.read()
        file_obj.close()
        template = json.loads(content)
        return template


    def process_message(self, message):
        # We'll process the message here. Important stuff can be cached using redis
        pass