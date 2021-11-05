"""
This module is for defining indexes of terms

Author : Ali Najafi
2021/10/21
14:44 pm
"""


import copy
import random
import math
from Preprocessing import DocumentGather,Preprocessor,DocumentFormatRouter,SimpleHandler

class PostingsList:
    def __init__(self,info_size = 30):
        self.docs = []
        self.size = 0
        self.info_size = info_size #for showing or printing postings list with limitaion
        self.maximum = -math.inf
    def addInfo(self,docID):
        """
        Adds docID to the Posting list
        respecting to the Ascending order.
        """
        
        if not self.docs :
            self.docs.append(docID)
            self.maximum = docID
            self.size += 1
        elif docID > self.maximum :
            self.docs.append(docID)
            self.maximum = docID
            self.size += 1
        elif docID == self.maximum :#doc ID is already in the postings list
            pass 
        else :
            for docid in self.docs :
                
                if docID < docid:
                    bigger_number_indx = self.docs.index(docid)
                    self.docs.insert(bigger_number_indx,docID)
                    self.size += 1
                    break
                elif docid == docID:# if doc id is already in the docs. 
                                    #there is no need to add it agin.
                    break

    def __str__(self):
        temp = f'< {self.size} ,<'
        for d in self.docs:
            if d != self.docs[-1]:#if its not last item put ','
                if self.docs.index(d) > self.info_size:
                    #self.docs is too big to show
                    temp += f' ... {self.size - self.info_size } more DocIDs'
                    break
                temp += str(d) + ','
            else :
                temp += str(d) + '> >'
                
        return temp
                             

class InvertedIndex:
    """
    Saves terms and their doc_id s to
    access terms easily.
    """
    def __init__(self,info_show_limit = 30):
        self.dictionary = {}
        self.size = 0
        self.limit = info_show_limit
    
    def check_types(self,term=None,doc_id=None):
        if term:
            if type(term) != type(str) :
                raise TypeError(f'Term\'s type should be string.{term.__class__.__name__} given.')
        if doc_id:
            if type(doc_id) != type(int):
                raise TypeError(f'Document ID should be an integer but {doc_id.__class__.__name__} given.')
    
    def addTerm(self,term:str,doc_id:int,raise_error : bool = False):
        """
        whith this method we can add
        term and it's doc id in the dictionary.

        if any error occures raise_error tells
        raise it or not.
        """
        if raise_error :
            self.check_types(term,doc_id)
        postings = self.dictionary.get(term)
        if not postings :
            self.dictionary[term] = PostingsList(info_size=self.limit)  
            self.dictionary[term].addInfo(doc_id)
        else :
            postings.addInfo(doc_id)
    
    def addTerms(self,terms:[(int,[str])],raise_error:bool = False):
        """
        add bunch of terms to dictionary.
        the format should be like:
        [(doc_id,[terms1,terms2,...]),...]
        exp : [
        (1,
        ['hello','world']),
        (2,
        ['love','some','buy']),
        .
        .
        .
        ]
        """
        if raise_error :
            self.check_types()

        for doc_id,words in terms :
            for term in words :
                self.addTerm(term,doc_id)
        
    def termsCount(self):
        return len(self.dictionary.keys())
    
    def getTermDocIDs(self,term:str):
        """
        return a specific term's postings list
        """
        p_list = self.dictionary.get(term)
        if p_list:
            return p_list.docs
        return []
        

    def getTerms(self,limit=None):
        res = []
        if not limit :
            limit = len(self.dictionary.keys()) -1
        return list(self.dictionary.keys())[:limit]
    
    def getTermsPosts(self,limit=None):
        """
        returns all terms with their posting list
        as [(term,postingslist)] if limit not set
        """
        res = []
        if not limit :
            limit = len(self.dictionary.keys()) -1
        c=0
        for term,p in self.dictionary.items():
            if c > limit :
                break
            item = (term,p.docs,)
            res.append(item)
        return res
        
    
    def __str__(self):
        result = ''
        c = 0
        for term,postings in self.dictionary.items():
            if c > self.limit :
                break
            result += term
            result += ' : ' + postings.__str__()
            result += '\n'
            c+=1
        return result





if __name__ == '__main__':
    pass


    
