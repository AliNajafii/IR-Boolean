
import threading
from nltk.tokenize import word_tokenize


def parse(text,sep='()'):
    stack = []
    for char in text:
        if char == sep[0]:
            #stack push
            stack.append([])
        elif char == sep[1]:
            yield ''.join(stack.pop())
        else:
            #stack peek
            stack[-1].append(char)

class ListFullError(Exception):
    pass
class ListWrongInit(Exception):
    pass

class SafeSingleton:
    """
    This singleton is safe. 
    supper classes cant change the subclass's
    instance and vice versa.
    the instance of  each class is
    created like : ClassName_instance
    """
    _lock = threading.Lock()
    def __new__(cls):
        with cls._lock :
            instance = f'{cls.__name__}_instance'
            if not hasattr(cls,instance):
                new = super(SafeSingleton,cls).__new__(cls)
                setattr(cls,instance,new)
        return getattr(cls,instance)
    
    def __setattr__(self,name,value):
        if name == '__name__':
            raise AttributeError('Can not change __name__ attribute')
        super().__setattr__(name,value)


class LimitedList(list):
    def __init__(self,limit,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.limit = limit
        self.size = 0
        self.check_init()
    
    def append(self,data):
        self.size += 1
        self.check_limit()
        super().append(data)
    
    def insert(self,position,value):
        self.size += 1
        self.check_limit()
        super().insert(position,value)
    
    def remove(self,obj):
        super().remove(obj)
        self.size -= 1
        self.check_limit()
    
    def pop(self,indx,value):
        res = super().pop(indx,value)
        self.size -= 1
        self.check_limit()
        return res

    def clear(self):
        super().clear()
        self.size = 0
    
    def extend(self,iterable):
        elems_left = self.limit - self.size
        it_len = len(iterable)
        if elems_left >= it_len:
            super().extend(iterable)
            self.size += it_len
            self.check_limit()
        else :
            raise ListFullError(f'List is Full .(limit = {self.limit})')
    
    def check_limit(self):
        if self.size > self.limit :
            raise ListFullError(f'List is Full .(limit = {self.limit})')
    
    def check_init(self):
        c = len(self)
        if  c > self.limit:
            raise ListWrongInit(f'element limit is {self.limit} but {c} elements given.')
        self.size = c



if __name__ == '__main__':
    text = '(((a and b) or c) and (d and (not e or f)))'
    s=parse(text)
    res = []
    for exp in list(s):
        res.append(word_tokenize(exp))
    print(res)
    