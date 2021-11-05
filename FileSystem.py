"""
Author : Ali Najafi
2021/10/16
17:00 pm
"""
import abc
from typing import List,Generator
import os
import math
from utils import LimitedList,SafeSingleton,ListFullError
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

class Extractable:
    """
    all objects that could 
    get data and are source of data
    like : file , image , video , ...
    """
    @abc.abstractmethod
    def getRaw(self):
        pass

class DocID(SafeSingleton):
    """
    This class is a Singleton pattern
    to update the id of files automatically
    """
    __id = 0
    step = 1
    def __new__(cls):

        if hasattr(cls,f'{cls.__name__}_instance'):
                cls.__id += cls.step
                return cls.__id
        else :
            cls.__id += cls.step
            super().__new__(cls)
            return cls.__id
    @classmethod        
    def get_id(cls):
        return cls.__id
  

class CrawlerInterFace(abc.ABC):

    @abc.abstractmethod 
    def crawl(self):
        pass

class AbstractCrawler(CrawlerInterFace):
    def __init__(self,path):
        self._files : Generator = None
        self.path = path
    @abc.abstractmethod
    def get_items(self,count : int):
        pass
    def normalize_path(self):
        self.path = os.path.normpath(self.path)
    
    def pre_crawl(self):
        """
        this method is run before crawling
        """
        self.normalize_path()

    @abc.abstractmethod
    def _crawl(self):
        """
        main buisinnes logic of crawling here
        """
    
    def crawl(self):
        self.pre_crawl()
        self._crawl()


class AbstarctFile:
    def __init__(self,name,formt,path,size = None):
        self.name = name
        self.formt = formt
        self.path = path
        self.is_busy = False
        self.size = size

    @abc.abstractmethod
    def getSize(self):
        pass

class File(AbstarctFile):
    size_formats = ('B','KB','MB','GB','TB','ULTRA')

    def getSize(self,in_ = 'mb'):
        """
        get size of file (size,size_format)
        """
        if 0<self.size<1000 :
            return (self.size,'B')
        elif 1000 <= self.size <10**6:
            return (self.size/1000,'KB')
        elif 10**6 <= self.size < 10**9:
            return (self.size/10**6,'MB')
        elif 10**9 <= self.size < 10**12 :
            return (self.size/10**9,'GB')
        elif 10**12 <= self.size < 10**15:
            return (self.size/10**12,'TB')
        else :
            return (math.inf,'ULTRA')
        
    def getFullPath(self):
        return os.path.abspath(os.path.join(self.path,self.getFullName()))
    
    def getFullName(self):
        return self.name + '.'+ self.formt
    
    def __str__(self):
        s = self.getSize()
        return f'<File {self.getFullName()} {s[0]} {s[1]}>'
    
    def __eq__(self,other):
        return self.getFullPath() == other.getFullPath()



class FileCrawler(AbstractCrawler):
    """
    this class is useful for crawling 
    in a directory to gadering files
    """

    def __init__(self,path,skip_formats = None):
        super().__init__(path)
        self.current_root = None
        self.last_file = None
        self.skip_formats = skip_formats if skip_formats else []
        

    def _crawl(self):
        self._files = os.walk(self.path)
    
    def getFiles(self):
        """
        get crawled generator files in
        os.walk method format
        """
        return self._files
    
    def file_format_extractor(self,name:str):
        parsed = name.split('.')
        formt = parsed.pop()
        f_name = ''
        for other in parsed:
            f_name += other
            if not other == parsed[-1]:
                f_name+='.'
        
        return(f_name,formt)
    
    def get_items(self,count:int=None,as_doc = True):
        """
        return File class objects generator
        """
        res = []
        c = 0
        while True:
            try:
                root,dirs,files = next(self._files)
            except StopIteration:
                break
            if count : #for when count limit is set
                if c > count :
                    break
            for file in files :
                name ,formt = self.file_format_extractor(file)
                if formt not in self.skip_formats:
                    size = os.path.getsize(os.path.join(root,file))
                    yield File(name,formt,root,size)
                    c+=1
                    


class Document(Extractable):
    """
    is the unit of processing in IR system.
    """
    def __init__(self,file:AbstarctFile):
        self.ID = DocID()
        self.data = file
    
    def getRaw(self,mode='r',encoding = None):
        d = None
        with open(self.data.getFullPath(),mode,encoding = encoding) as f :
            d = f.read()
        
        return d
    
    def getID(self):
        return self.ID
    
    
    def __str__(self):
        return f'{self.getID()},{self.data.path},{self.data.getFullName()}'


class DocumentGather:
    """
    This class gathers Apropriate files 
    from a path with best performance
    it uses Limited Buffer to 
    reduce memory usage.
    """

    def __init__(self,path:str,
        crawler:AbstractCrawler = FileCrawler,
        doc_type : Document = Document,
        files_limit:int = None,skip_formats = None,
        ):
        self.path = path
        self.limit = files_limit
        self.last_path = self.path
        self.docs = LimitedList(self.limit) if self.limit else []
        self.buffer_full = False
        self.crawler = crawler
        self.Doc = doc_type
        self._crawled = None
        self.skip_formats = skip_formats
        self.nth_file = 0
        self.doc_table = DocumentHashTable()
        
    
    def setup(self):
        self.crawler = self.crawler(self.path,skip_formats = self.skip_formats)
        self.crawler.crawl()
    
    def updatePath(self,path):
        self.path = path
    
    def gather_nolimit(self):
        """
        gathers files as documents.
        it returns all files of the path to self.files
        """
        docs = []
        for f in self.crawler.get_items():
            doc = Document(f)
            docs.append(doc)
            self.doc_table.addDoc(doc)
            
        
        return docs

        
    
    def gather(self,limit_number = 200):
        """
        it returns limited number of files.
        you can use it agin to start from 
        last file readen.
        """

        raise NotImplementedError('Not Implemented yet.')

    def getDocByID(self,doc_id:int):
        return self.doc_table.getDoc(doc_id)
    


class DocumentHashTable:
    """
    to saving  documents ID and actual document
    object. 
    with this table we can access doc objects 
    by id.
    """
    def __init__(self):
        self.hash_table = {}
    
    def addDoc(self,doc : Document):
        doc_id = doc.getID()
        self.hash_table.update({doc_id:doc})
    
    def getDoc(self,doc_id:int):
        return self.hash_table.get(doc_id)
    
    def getAllDocIDs(self):
        return list(self.hash_table.keys())


        
    

     
if __name__ == "__main__":
    # def on_created(event):
    #     print(os.path.join(os.path.abspath(),event.src_path))

    # patterns = ["*"]
    # ignore_patterns = None
    # ignore_directories = False
    # case_sensitive = True
    # my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
   
    # my_event_handler.on_created = on_created
    # import time
    # path = "."
    # go_recursively = True
    # my_observer = Observer()
    # my_observer.schedule(my_event_handler, path, recursive=go_recursively)

    # my_observer.start()
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     my_observer.stop()
    #     my_observer.join()
    pass





    