"""
this module is for parsing and executing boolean queries

Author : Ali Najafi
2021/10/23
19:10 pm
"""
from typing import List
import abc 
from utils import LimitedList
from time import sleep
from nltk.sem.logic import (
    AndExpression,
    OrExpression,
    IndividualVariableExpression as TermExpression,
    NegatedExpression,
    ConstantExpression as WordExpression,
    Variable
)
from InvertedIndex import InvertedIndex
from nltk.sem.logic import LogicParser
from FileSystem import DocumentGather
from Preprocessing import DocumentFormatRouter, Preprocessor ,SimpleHandler
from FileSystem import DocumentHashTable

QUERY_VARAIBLES_TYPES = (WordExpression,TermExpression,)

class OpratorNotSupported(Exception):
    pass

class ParserInterface(abc.ABC):
    
    @abc.abstractmethod
    def parse(self):
        pass
class AbstractBaseParser(ParserInterface):
    def __init__(self,data):
        self.data = data # data for pasre


class Executable(abc.ABC):
    @abc.abstractmethod
    def execute(self):
        pass

class BNode:
    """
    B-Tree node.
    """
    def __init__(self,data,parent=None):
        self.parent = parent
        self.right_child = None
        self.left_child = None
        self.data = data
    
    def addRightChild(self,node):
        self.right_child = node
        node.parent = self

    def addLeftChild(self,node):
        self.left_child = node
        node.parent = self

    def removeChild(self,node):
        if self.right_child == node:
            self.right_child = None
            return True
        else :
            self.left_child = None
            return True
        return False
                                                

    def getParent(self):
        return self.parent

    def getParents(self,parent,plist=None,c=0):
        print(self,c)
        if not plist:
            plist = []
        if not parent.isRoot():
            plist.append(self.parent)
            print(plist[c])
            sleep(2)
            self.getParents(parent,plist,c+1)
        return plist


        


    def isLeaf(self):
        return self.left_child == None and self.right_child == None
    def isRoot(self):
        return not self.parent
    
    def __str__(self):
        return f'<BNode {self.data}>'

    
class BooleanQueryParser(AbstractBaseParser):
    """
    parses the Boolean query by parse tree
    which is a composite .
    it reads the query and make ExpresionStack
    """
    def __init__(self,query):
        self.query = query
        self.b_tree = None

    def _parse(self,exp=None):
        if not exp :
            if isinstance(self.b_tree.data,QUERY_VARAIBLES_TYPES) :# it is just a single varaible query
                return self.b_tree
            exp = self.b_tree

        if isinstance(exp.data,NegatedExpression):
            if not isinstance(exp.data.term,QUERY_VARAIBLES_TYPES):
                left = BNode(exp.data.term)
                exp.addLeftChild(left)
                self._parse(left)
            
        elif isinstance(exp.data.first,QUERY_VARAIBLES_TYPES) and not isinstance(exp.data.second,QUERY_VARAIBLES_TYPES):
            left = BNode(exp.data.first)
            right = BNode(exp.data.second)
            exp.addLeftChild(left)
            exp.addRightChild(right)
            self._parse(right)
        elif not isinstance(exp.data.first,QUERY_VARAIBLES_TYPES) and isinstance(exp.data.second,QUERY_VARAIBLES_TYPES):
            left = BNode(exp.data.first)
            right = BNode(exp.data.second)
            exp.addLeftChild(left)
            exp.addRightChild(right)
            self._parse(left)
        
        elif not isinstance(exp.data.first,QUERY_VARAIBLES_TYPES) and not isinstance(exp.data.second,QUERY_VARAIBLES_TYPES): 
            left = BNode(exp.data.first)
            right = BNode(exp.data.second)
            exp.addLeftChild(left)
            exp.addRightChild(right)
            self._parse(left)
            self._parse(right)


    def parse(self):
        self.clean_query()
        self._parse()
        return self.b_tree

    def clean_query(self):
        if not isinstance(self.query,str):
            raise ValueError(f'query should be string not {self.query.__class__.__name__}')
        
        self.query = self.query.lower()
        standard = LogicParser().parse(self.query)
        self.b_tree = BNode(standard)

        

class BoolOprator:
    """
    base class of Boolean Oprator.
    Boolean Oprator oprates on two or one 
    postingLists .
    """
    oprand_num = None
    def __init__(self,oprand1,oprand2=None):
        self.left = oprand1
        self.right = oprand2
        self.check_oprands()
    
    def check_oprands(self):
        if not self.oprand_num:
            raise ValueError('Set oprand_num')
        if self.oprand_num == 2 :
            if not self.left and not self.right:
                raise ValueError(f'{self.__class__.__name__} BoolOprator needs 2 oprands')
        elif self.oprand_num == 1 :
            if not self.left :
                raise ValueError(f'self.__class__.__name__ BoolOprator needs 1 oprands')
            elif self.right :
                raise ValueError(f'self.__class__.__name__ BoolOprator needs 1 oprands not 2.')

    def oprate(self):
        pass

class And(BoolOprator):
    oprand_num = 2
    def oprate(self):
        iter1 = iter(self.left)
        iter2 = iter(self.right)
        p1_stopped = False
        p2_stopped = False
        result = []
        p1_next = next(iter1)
        p2_next = next(iter2)
        while not p1_stopped and not p2_stopped:
            if p1_next == p2_next:
                result.append(p1_next)
                try:
                    p1_next = next(iter1)
                except StopIteration :
                    p1_stopped = True
                try:
                    p2_next = next(iter2)
                except StopIteration:
                    p2_stopped = True
            elif p1_next < p2_next:
                try:
                    p1_next = next(iter1)
                except StopIteration :
                    p1_stopped = True
            
            else :
                try:
                    p2_next = next(iter2)
                except StopIteration:
                    p2_stopped = True
        
        return result

class Or(BoolOprator):
    oprand_num = 2
    def oprate(self):
        s1 = set(self.left)
        s2 = set(self.right)
        s3 = s1.union(s2)
        return sorted(s3)

class AndNot(BoolOprator):
    oprand_num = 2
    def oprate(self):
        """
        calculates the p1 AND NOT P2
        """
        if not self.left and not self.right :
            return []
        elif not self.right :
            return self.left
        elif not self.left :
            return []
        iter1 = iter(self.left)
        iter2 = iter(self.right)
        p1_stopped = False
        p2_stopped = False
        result = []
        p1_next = next(iter1)
        p2_next = next(iter2)
        while not p1_stopped and not p2_stopped:
            if p1_next == p2_next:
                try:
                    p1_next = next(iter1)
                except StopIteration :
                    p1_stopped = True
                try:
                    p2_next = next(iter2)
                except StopIteration:
                    p2_stopped = True

            elif p1_next < p2_next:
                try:
                    result.append(p1_next)
                    p1_next = next(iter1)
                except StopIteration :
                    p1_stopped = True
            
            else :
                try:
                    p2_next = next(iter2)
                except StopIteration:
                    p2_stopped = True

        
        return result

class Not(BoolOprator):
    oprand_num = 1
    def oprate(self,index:InvertedIndex,all_doc_ids):
        if isinstance(self.left,str):
            left_docs = index.getTermDocIDs(self.left)
        elif isinstance(self.left,list):
            left_docs = self.left
        return [doc_id for doc_id in all_doc_ids if doc_id not in left_docs]


BASIC_BOOL_OPS = [And,Or,AndNot]
ALL_BOOL_OPS = [And,Or,Not,AndNot]

class QueryExecutor(Executable):
    """
    executes the queries 
    by itrating B-tree and oprating
    on each expression.
    it represents the docid of terms.
    """

    def __init__(self,
    index : InvertedIndex,
    document_map : DocumentHashTable,
    parser = BooleanQueryParser,
    oprators = BASIC_BOOL_OPS,
    ):
        self.parser_type = parser
        self.doc_table = document_map
        self.parser = None
        self.query = None 
        self.parsed_postorder = [] #expressions wich made by itrating postorder of parse tree
        self.b_tree = None
        self.index = index
        self.oprators = oprators
        self._check()
    
    def _check(self):
        if not all(type(op) == type(BoolOprator) for op in self.oprators):
            raise TypeError('Oprators should be Boolean Oprator')
        if not type(self.query) == str :
            TypeError('Query should be string not {self.query.__class__.__name__}.(you should use search instead of execute.)')
        if not type(self.parser_type) == type(AbstractBaseParser) :
            raise TypeError('Parser should be any kind of AbstractBaseParser not {self.parser.__class__.__name__}')
    
    def oprator_mapper(self,exp = None,symbol=None):
        """
        mapps the Expression classes or symbols given
        to appropriate oprator.
        exp and symbol could not given at same time.
        """
        if exp.__class__ == AndExpression :
            if And in self.oprators :
                return And
            else :
                raise OpratorNotSupported(f'supported oprators are {self.oprators}')
        elif exp.__class__ == OrExpression :
            if Or in self.oprators :
                return Or
            else :
                raise OpratorNotSupported(f'supported oprators are {self.oprators}')
        elif exp.__class__ == NegatedExpression :
            if Not in self.oprators :
                return Not
            else :
                raise OpratorNotSupported(f'supported oprators are {self.oprators}') 
    
    
    def oprator_handler(self,oprator,*variables):
        """
        this method handles the oprations
        executions and return the result of each
        one
        """
        postings = []
        if oprator == Or :
            for v in variables:
                if isinstance(v,str):
                    posts = self.index.getTermDocIDs(v)
                    postings.append(posts)
                elif isinstance(v,list):
                    postings.append(v)
            if all([i==[] for i in postings]):
                return []
            elif not postings[0]: #if first post list is Null result would be second
                return postings[1]
            elif not postings[1]:#if second post list is Null result would be first
                return postings[0]
            return Or(*postings).oprate()
        
        elif oprator == And :
            
            for v in variables :
                if isinstance(v,str):
                    posts = self.index.getTermDocIDs(v)
                    postings.append(posts)
                elif isinstance(v,list):
                    postings.append(v)
            if all(i==[] for i in postings):# if all two post lists are Null result would be null.
                return []
            elif any(i==[] for i in postings):#if one of the post list is Null result would be Null.
                return []
            return And(*postings).oprate()

        elif oprator == AndNot :
            for v in variables:
                if isinstance(v,str):
                        posts = self.index.getTermDocIDs(v)
                        postings.append(posts)
                elif isinstance(v,list):
                        postings.append(v)
                
            return AndNot(*postings).oprate()
            
        elif oprator == Not:
            v = variables[0]
            if not isinstance(v,str) and not isinstance(v,list):
                raise TypeError(f'Not oprator accepts just terms as oprand not {type(v)}')
            all_doc_indexs = self.doc_table.getAllDocIDs()
            return Not(v).oprate(self.index,all_doc_indexs)

    def get_query_variables_name(self,exp):
        
        result = []
        for v in exp.variables() :
            if v.name not in result:
                result.append(v.name)
        for c in exp.constants():
            if c.name not in result:
                result.append(c.name)
        return result   

    def is_two_sentence(self,exp):
        """
        returns true if expression has two sentences
        like : a and b --> True
        """

        try :
            if isinstance(exp.first,QUERY_VARAIBLES_TYPES) and isinstance(exp.second,QUERY_VARAIBLES_TYPES):
                return True
            return False
        except AttributeError:
            return False
    
    def is_single_varaible_expression(self):
        if len(self.parsed_postorder) == 1 :
            exp = self.parsed_postorder[0]
            if isinstance(exp,QUERY_VARAIBLES_TYPES):
                return True
        return False
    
    def execute(self):
        self._check()
        self.parsed_postorder.clear()
        parser = self.parser_type(self.query)
        self.b_tree = parser.parse()
        self._postorder(self.b_tree)
        print('Parsed query: ',self.parsed_postorder)

        if self.is_single_varaible_expression():#checking for single expression like: hello
            name = self.get_query_variables_name(self.parsed_postorder[0]) #extract varible names
            return self.index.getTermDocIDs(name[0]) #returning the doc posintings list of single varaible expression
        value_stack = []

        for exp in self.parsed_postorder:
            oprator = self.oprator_mapper(exp)

            if isinstance(exp,QUERY_VARAIBLES_TYPES) :
                name = self.get_query_variables_name(exp)
                value_stack.append(name[0])

            elif isinstance(exp,NegatedExpression):
                var_names = self.get_query_variables_name(exp)
                if len(var_names) == 1 :
                    oprator = Not
                    result = self.oprator_handler(oprator,*var_names)
                    value_stack.append((exp,result))

                else :
                    result = value_stack.pop()
                    if isinstance(result,tuple): #negated expression
                        _,result = result
                        value_stack.append(result)
                    else :#push the result of inner expression of negativ expression
                            #like not(a and b) or c --> a and b is inner expression
                            #and should be labeled as negative.
                            # 'result' is inner expression result
                        result = self.oprator_handler(Not,result) #inner expression should be negated
                        value_stack.append(('Inner Expression of Nigated Expression',result))
                    
                    

            elif self.is_two_sentence(exp):
                
                var_names = self.get_query_variables_name(exp)
                
                result = self.oprator_handler(oprator,*var_names)
                value_stack.append(result)
            else :
                second = value_stack.pop()
                first = value_stack.pop()

                if isinstance(first,tuple) and isinstance(second,tuple) : #two not expression is being to oprate
                                                                            # like not(a or b) and not(d and b)
                    #compute not of first negativ and seconf negativ and then And them
                    
                    res_first = first[1]
                    res_second = second[1]
                    result = self.oprator_handler(oprator,res_first,res_second)
                    value_stack.append(result)                           

                elif isinstance(first,tuple):#negative expression
                    _ , first_result = first
                    result = self.oprator_handler(oprator,second,first_result)
                    value_stack.append(result)

                elif isinstance(second,tuple) :#negative expression
                    print('second is negative')
                    _ , second_result = second
                    result = self.oprator_handler(oprator,first,second_result)
                    value_stack.append(result)

                                        
                else :
                    result = self.oprator_handler(oprator,first,second)
                    value_stack.append(result)
                    

        result  = value_stack.pop() #last result is the whole result
        if isinstance(result,tuple): # when we have just one not expression
            return result[1]
        
        return result

        

    
    def search(self,query):
        self.query = query
        return self.execute()


    def _postorder(self,b_tree : BNode):
        
        if b_tree :
            self._postorder(b_tree.left_child)
            self._postorder(b_tree.right_child)
            self.parsed_postorder.append(b_tree.data)




if __name__ == '__main__':
    # from time import time
    # path = './toy-data'
    # index = InvertedIndex()
    # gatherer = DocumentGather(path)
    # gatherer.setup()
    # t1 = time()
    # files = gatherer.gather_nolimit()
    # t2 = time() - t1

    # router = DocumentFormatRouter(files,handlers=[SimpleHandler,])
    # t7 = time()
    # data = router.extract_data()
    # t8 = time() - t7

    # p = Preprocessor()
    # p.setup(data,allow_punctuatins='?-',stop_words=[])
    # t3 = time()
    # data = p.process()
    # t4 = time() - t3

    # t5 = time()
    # index.addTerms(data,raise_error=True)
    # t6 = time() - t5

    # r = And([1,2,3,6,7,8],[3])
    # print(r.oprate())
    
    # mapp = gatherer.doc_table
    # qe = QueryExecutor(index,mapp,oprators=ALL_BOOL_OPS)
    
    # t9 = time() 
    # res = qe.search('not(fse and institute)')
    # t10 = time() - t9
    
    # for d_id in res:
    #     doc= mapp.getDoc(d_id)
    #     name = doc.data.getFullName()
    #     print(name)
    
        

    # print(index)
    # print('--------------------------')
    # print(f'{len(res)} results found in {t10} s')
    # print(f'data gather : {t2} s')
    # print(f'extracting : {t8}')
    # print(f'preprocess : {t4} s')
    # print(f'indexing : {t6} s')
    # print(f'total : {t2+t4+t6+t8+t10} s')
    pass
    
    
    

   


    
