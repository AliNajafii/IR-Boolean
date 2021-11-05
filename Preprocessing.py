"""
This module has functionalities which can 
be helpful for preprocessing files

Author : Ali Najafi
2021/10/19
18:20 pm
""" 


import abc
from time import time
from typing import Any
from FileSystem import File,DocumentGather,Document
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer,LancasterStemmer
from nltk.tokenize import word_tokenize
from string import punctuation

class PreprocessorInterFace(abc.ABC):
    @abc.abstractmethod
    def process(self):
        pass

class DataExtractor:
    """
    this Abstract class is for defining extractor classes
    """
    @abc.abstractmethod
    def extract_data(self):
        pass


class FormatHandler(DataExtractor):
    """
    this class handels the format of the file and returns 
    the apropriate data .
    """
    formats = [] #it's when a format has more than one abbriviation like .doc and .docx
    name = None
    
    def __init__(self,file : File):
        self.file = file

    def __str__(self):
        return f'<{self.name}Handler {",".join(self.formats)}>'
    
    def __repr__(self):
        return self.__str__()

class PDFHandler(FormatHandler):
    """
    Handels the PDF format files 
    and extract data of it.
    it's like a Facade Design Pattern
    it connects to file format libraries. 
    """
    formats = ['pdf',]
    name = 'PDF'
   

class HTMLHandler(FormatHandler):
    """
        Handels the HTML format files 
        and extract data of it.
        it's like a Facade Design Pattern
        it connects to file format libraries.
    """
    formats = ['htm','html','xhtml','jhtml']
    name = 'HTML'

   

class DOCXHandler(FormatHandler):
    """
    it handels .docx , .doc , ppt formats 
    like MSWord files.
    it's like a Facade Design Pattern
    it connects to file format libraries.
    """
    formats = ['docx','doc','ppt','pptx']
    name = 'MsWord'


class CodeHandler(FormatHandler):
    """
    it handles code formats like .py, .c , .h or ...
    it's like a Facade Design Pattern
    it connects to file format libraries.
    """

    formats = [
    'py','c','php','lua',
    'asp','jsp','jspx',
    'md','js','cgi',
    ]
    name = 'Code'


class SimpleHandler(FormatHandler):
    """ it handels simple formats like .txt
    with cp1256 encoding.
    it's like a Facade Design Pattern
    it connects to file format libraries
    """
    name = 'Simple'
    
    def extract_data(self):
        path = self.file.getFullPath()
        with open(path,'r') as f:
            data = f.read()
            f.close()
        
        return data

class XMLHandler(FormatHandler):
    """handles xml format"""
    name = 'XML'
    formats = ['xml','rss','svg']


class DocumentFormatRouter(DataExtractor):
    """
    This class make Routes to 
    best DataExtractor depending on
    the document has which kind of format.

    this class uses handlers like Chain of Responsiblty pattern
    to handle format in a best way.

    there is no need of initializing handlers 
    and this class can implicitly.

    you can make priotry for hanler checking
        for example if you think most of your docs
        are .pdf insert PDFHandler in the first index of
        handlers.
    """
 

    def __init__(self,docs : [Document] = None, handlers : [FormatHandler] = None):

        if handlers :
            if all(type(h) == type(FormatHandler) for h in handlers):
                self.handlers = handlers
            else :
                raise ValueError(f'all handlers should be FormatHandlers.\n{handlers}')

        else :
            self.handlers = (
                PDFHandler,
                DOCXHandler,
                HTMLHandler,
                XMLHandler,
                CodeHandler,
                SimpleHandler,
            )

        # if not docs :
        #     raise ValueError('give at least one file')
        self.docs = docs
        

    def getHandler(self,file : File):
        for h in self.handlers :
            if file.formt in h.formats:
                return h
        return SimpleHandler

    def extract_data(self,of_specific : Document = None):
        """
        returns data of all files 
        in list.
        """
        data = []
        if of_specific:
            handler_type = self.getHandler(of_specific)
            if handler_type:
                handler = handler_type(file=of_specific)
            return [(of_specific.getID, handler.extract_data())]
        
        for doc in self.docs :
            handler_type = self.getHandler(doc.data)
            handler = handler_type(doc.data)
            data.append((doc.getID(),handler.extract_data()))
        
        return data

class Preprocessor(PreprocessorInterFace):
    """
    Abstract Base class of 
    Preprocessing phase
    """
    def __init__(self):
        self.lower = True
        self.stop_words = stopwords.words('english')
        self.stemmer = None
        self.punctuations = punctuation
        self.configed = False
        self.processed = []
    
    def setup(
            self,data_set,
            stop_words = None,
            stemmer =None,
            punctuations : str =None,
            ignore_case : bool= True,
            allow_punctuatins : str = None
        ):
        if stop_words != None:
            self.stop_words = stop_words
        if stemmer:
            self.stemmer = stemmer
        if punctuations :
            if allow_punctuatins:
                table = punctuations.maketrans('','',allow_punctuatins)
                punctuations = punctuations.translate(table)
                self.punctuations = punctuations
        elif allow_punctuatins:
            table = self.punctuations.maketrans('','',allow_punctuatins)
            self.punctuations = self.punctuations.translate(table)


        if not ignore_case :
            self.lower = False
        self.configed = True
        self.data_set = data_set


    def check(self):
        if not self.data_set :
            raise ValueError('Can\'t process without data set.')
        if not hasattr(self.stop_words,'__iter__') :
            raise ValueError(f'stopwords should be itrable but {self.stop_words.__class__.__name__} given.')
        if not self.configed :
            raise Exception('did not setup. setup for process.')
       
        
    def tokenize(self,raw:str):
        data = raw
        if self.lower :
            data = data.lower()
        if self.punctuations :
            data = self.delete_puncs(data)
        words = [w for w in word_tokenize(data) if w not in self.stop_words]
        return words
        
    def make_stems(self,words):
        results = []
        if not self.stemmer:
            return words
        for w in words:
            results.append(self.stemmer.stem(w))
        return results


    def delete_puncs(self,raw:str):
        
        table = raw.maketrans('','',self.punctuations)
        data = raw.translate(table)
        return data
    
    
    def process(self):
        """
        returns tokens
        of a document in this format if document_gather is set:
        [(docid,[*words]),...]
        else you should give data list in setup
        """
        self.check()

        for doc_id , data in self.data_set :
            cleaned_tokens = self.tokenize(data)
            words = self.make_stems(cleaned_tokens)
            self.processed.append((doc_id,words))
        return self.processed



if __name__ == '__main__':
    # path = './test'
    # dg = DocumentGather(path)
    # dg.setup()
    # t1 = time()
    # files = dg.gather_nolimit()
    # t2 = time() - t1

    # router = DocumentFormatRouter(files,handlers=[SimpleHandler,])
    # t3 = time()
    # data = router.extract_data()
    # t4 = time() - t3
    
    # p = Preprocessor()
    # p.setup(data_set=data,allow_punctuatins='\'?-')

    # t5 = time()
    # results = p.process()
    # t6 = time() - t5
    # print(results)
    # print(len(data),'files data extracted.')
    # print('file Gathering',f'took {t2} s')
    # print('extracting data ',f'took {t4} s')
    # print('preprocessing took',f'{t6} s')
    # print(f'total time : {t2 + t4 + t6}')
    pass
   

