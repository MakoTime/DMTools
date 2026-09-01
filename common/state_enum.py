from enum import Enum

class StateEnum(Enum):
    
    @property
    def last(self):
        return list(self)[-1] if list(self) else None
    
    def next(self):
        members = list(self)
        index = members.index(self)
        return members[index + 1] if index + 1 < len(members) else None
    
    def previous(self):
        members = list(self)
        index = members.index(self)
        return members[index - 1] if index - 1 >= 0 else None