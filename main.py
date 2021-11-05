"""
This module is for running the main system

Author : Ali Najafi
2021/10/24
13:20 pm
"""

from FileSystem import DocumentGather,AbstractCrawler,FileCrawler,Document
from Preprocessing import Preprocessor,DocumentFormatRouter,FormatHandler,SimpleHandler
from Query import QueryExecutor,ALL_BOOL_OPS
from InvertedIndex import InvertedIndex
from time import time
from nltk.stem import LancasterStemmer
from nltk.sem.logic import ExpectedMoreTokensException,LogicalExpressionException
import os

class BooleanSearchSystem:
    """
    This class manages the whole 
    mechanism of searching by controling
    DocumentGathering system,dataExtractors and format handlers
    preprocess systems and QueryExecutors
    and at last show the results
    """

    def __init__(self,sources_path:str,store_path:str):
        self.path = sources_path
        self.exists = os.path.exists(self.path)
        if not self.exists:
            print('Directory not exists!')
        self.store_path = store_path
        self.index = None
        self.query = None
        self.gatherer = None
        self.document_router = None
        self.preprocessor = None
        self.query_exec = None
        self.last_results = []
        self.extracted = None
    
    def setup(self,index=None,
    document_gather=None,
    document_router=None,
    query_execuctor=None,
    preprocessor = None
    ):
        if index : 
            self.index = index
        if document_gather :
            self.gatherer = document_gather
        if document_router:
            self.document_router = document_router
        if query_execuctor :
            self.query_exec = query_execuctor
        if preprocessor:
            self.preprocessor = preprocessor
        
        self._check_types()

        return True

    def _check_types(self):
        pass

    def setup_preprocessor(self,
    lower=None,
    stop_words=None,
    stemmer =None,
    punctuations : str =None,
    allow_punctuatins : str = None
    ):
        
        self.preprocessor = Preprocessor()
        self.preprocessor.setup([1,2,3],
        stop_words=stop_words,
        stemmer=stemmer,
        punctuations=punctuations,
        allow_punctuatins= allow_punctuatins
        )
    

    def setup_doc_gather(self,
    crawler:AbstractCrawler = FileCrawler,
    doc_type : Document = Document,
    files_limit:int = None,skip_formats = None,
    ):
        self.gatherer = DocumentGather(self.path,
        crawler=crawler, doc_type=doc_type,
        files_limit= files_limit,skip_formats=skip_formats
        )
        self.gatherer.setup()

    def setup_extractor(self,files=None,
    handlers : [FormatHandler] = None
    ):
        self.document_router = DocumentFormatRouter()
        if files :
            self.document_router.docs = files
        if handlers:
            self.document_router.handlers = handlers

    def setup_index(self,info_show_limit=30):
        self.index = InvertedIndex(info_show_limit)

    def start_gathering_docs(self):
        return self.gatherer.gather_nolimit()

    def preprocess(self,data_set):
        self.preprocessor.data_set = data_set
        try :
            res = self.preprocessor.process()
            return res
        except ValueError as e :
            print(f'Error : {e.args[0]}')
            print('hint : check the directory existance.')
        
            

    def search(self,query):
        try:
            res = self.query_exec.search(query)
            return res
        except LogicalExpressionException as e :
            print(f'Error : {e.args[0]}')
        
        
    
    def start(self,forever=False,show_file_names=True):
        t1 = time()
        docs = self.start_gathering_docs()
        t2 = time() - t1

        self.document_router.docs = docs
        t3 = time()
        extracted = self.document_router.extract_data()
        t4 = time() - t3
        
        t5 = time()
        preprocessed = self.preprocess(extracted)
        t6 = time() - t5

        t7 = time()
        self.index.addTerms(preprocessed)
        t8 = time() - t7

        self.query_exec = QueryExecutor(self.index,self.gatherer.doc_table)
        self.query_exec.oprators = ALL_BOOL_OPS

        time_table = {
            f'Gathering {len(docs)} Documents took':t2,
            'Extracting data took':t4,
            'Preprocessing data took':t6,
            'Indexing Documents took':t8
        }
        self.info_show(**time_table)
        
        query = input('Please Enter Your Search Query : ')
        self.query = query
        t9 = time()
        result = self.search(query)
        t10 = time() - t9
        self.show_results(result,t10,by_file_name=show_file_names,store_to_file=True)
        while forever :
            query = input('Please Enter Your Search Query : ')
            self.query = query
            t9 = time()
            result = self.search(query)
            print(result)
            t10 = time() - t9
            self.show_results(result,t10,by_file_name=show_file_names,store_to_file=True)

    def info_show(self,*args,**kwargs):
        for k,v in kwargs.items() :
            print(k,': ',v,'s')
            print('-'*50)
    def show_results(self,res,time_took=None,by_id:bool=True,by_file_name:bool=False,store_to_file=False):
        file = None
        if store_to_file :
            file = open(self.store_path,'a')
            file.write(f'Search Query : {self.query}\n')
        if by_file_name:
            by_id = False
        if by_id :
            print(*res)
        elif by_file_name :
            mapp = self.gatherer.doc_table
            if res:
                for d_id in res:
                    doc= mapp.getDoc(d_id)
                    if doc:
                        name = doc.data.getFullName()
                        print(d_id,')',name,file=file)
                        print(d_id,')',name)
                    
        if time_took and res:
            print(f'{len(res)} results in {time_took} s\n',file=file)
            print(f'{len(res)} results in {time_took} s\n')
        
        print('-'*50,file=file)
        print('-'*50)
        
        if store_to_file:
            file.close()
    
if __name__ == '__main__':
    path = input('Enter the sources path : ')
    path = path.strip()
    boolean_search = BooleanSearchSystem(path,'./logs/results.txt')
    while not boolean_search.exists :
        path = input('Enter the sources path : ')
        path = path.strip()
        boolean_search = BooleanSearchSystem(path,'./logs/results.txt')

    boolean_search.setup_doc_gather(skip_formats=['exe','dll','h','c'])
    boolean_search.setup_extractor(handlers=[SimpleHandler,])
    boolean_search.setup_preprocessor(stop_words=[])
    boolean_search.setup_index(info_show_limit=200)
    boolean_search.start(forever=True)
    input()
    
    