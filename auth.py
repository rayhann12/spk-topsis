from data.users import users

def authenticate(username, password):
    for user in users:
        if user["username"] == username and user["password"] == password:
            return user
    return None
