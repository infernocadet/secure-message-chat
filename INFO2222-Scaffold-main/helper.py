def add_friend_request(current_user, friend_user):
    with Session() as session:
        friend_request = 