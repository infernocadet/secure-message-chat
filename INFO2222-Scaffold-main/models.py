'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''
from typing import Dict

# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0 
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        self.dict: Dict[str, int] = {}
        self.active_participants: Dict[int, set] = {}

    def create_room(self, session, sender: str, receiver: str) -> int:
        from db import create_room_in_db, find_room_with_users

        # check if there is an existing room with the two users
        existing_room_id = find_room_with_users(session, sender, receiver)
        if existing_room_id:
            self.dict[sender] = existing_room_id
            self.dict[receiver] = existing_room_id
            return existing_room_id

        # otherwise make a new room
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        self.active_participants[room_id] = set()

        # handle database insertion
        create_room_in_db(session, room_id, sender, receiver)

        return room_id

    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id
        self.active_participants[room_id].add(sender)

    def leave_room(self, user):
        if user in self.dict:
            room_id = self.dict[user]
            if user in self.active_participants[room_id]:
                self.active_participants[room_id].remove(user)
            if not self.active_participants[room_id]:  # If no active participants, cleanup
                del self.active_participants[room_id]
            del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
    def is_active(self, user: str):
        room_id = self.get_room_id(user)
        return room_id in self.active_participants and user in self.active_participants[room_id]
    

    