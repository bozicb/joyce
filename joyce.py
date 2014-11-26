#!/usr/bin/env python

import argparse 
import logging 
import glob
from os import getenv, path
from sklearn.svm import LinearSVC, SVC, NuSVC
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
import metadata
import cPickle
import numpy

def document(path): 
    with open (path, "r") as myfile:
        data=myfile.read().replace('\n', '')
    return data 

def create_corpus(files): 
    documents = []
    for p in files: 
        documents.append(document(p))
    # need to keep track of the source.
    return documents
    
def xvalidation_subsets(tfidf,features,k): 
    block = []
    length = tfidf.shape[0]
    size =  length / k 
    subsets = []
    ## lost tooth approach
    for i in xrange(size, length-size, size): 
        new_tfidf = numpy.concatenate([(tfidf[0:i]).toarray(),(tfidf[i+size:length]).toarray()],axis=0)
        new_features = features[0:i] + features[i+size:length]
        subsets.append((new_tfidf,new_features))

    return subsets

__LOG_FORMAT__ = "%(asctime)-15s %(message)s"
__LIB_PATH__ = getenv("HOME") + '/lib/Joycechekovgavin/'
__DEFAULT_PATH__ = __LIB_PATH__ + 'corpus/'
__LOG_PATH__ = __LIB_PATH__ + 'joyce.log'
if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='Playing with word embeddings.')
    parser.add_argument('--log', help='Log file', default=__LOG_PATH__)
    parser.add_argument('--train', help='Start training from DB', action='store_const', const=True, default=False)

    # Should we have this available for a single examination of a document?
    parser.add_argument('--examine', help='Examine a document', default=None)
    parser.add_argument('--backing-store', help='Path of svm backing store', default='backing_store.pkl')
    parser.add_argument('--cross-validations', help="number of cross-validation segments", default="5")
    parser.add_argument('--alg', help="One of SVC, LinearSVC, or NuSVC", default ='NuSVC')
    parser.add_argument('--params', help="Algorithm parameters as dictionary string", default='{}')
    parser.add_argument('--ngrams', help="Pair of min, max n-gram size", default='(3,3)')
    args = vars(parser.parse_args())
    
    # evaluate commandline params of python objects
    import ast
    args['params'] = ast.literal_eval(args['params'])
    args['ngrams'] = ast.literal_eval(args['ngrams'])

    # set up logging
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.basicConfig(filename=args['log'],level=logging.INFO,
                        format=__LOG_FORMAT__)
    
    #files = joyce + other
    if args['train']: 
        segments = metadata.get_training_segments()
        print "# of Segments: %s" % len(segments)
        features = metadata.get_joyce_or_not_features()
        print "# of Features: %s" % len(features) 

        vec = CountVectorizer(min_df=1, ngram_range=args['ngrams'], analyzer='char_wb')
        counts = vec.fit_transform(segments)
        
        transformer = TfidfTransformer() 
        
        tfidf = transformer.fit_transform(counts)

        # do we really want a linear? 
        best = None
        best_svm = None
        for (tfidf_n,features_n) in xvalidation_subsets(tfidf,features,int(args['cross_validations'])): 
            ## should pass params            
            if args['alg'] == 'SVC': 
                svm = SVC(**args['params'])
            elif args['alg'] == 'NuSVC':
                svm = NuSVC(**args['params'])
            elif args['alg'] == 'LinearSVC': 
                svm = LinearSVC(**args['params'])
            svm.fit(tfidf_n,features_n)
            score = svm.score(tfidf.toarray(),features)
            print "Current score: %s" % score
            if not best or best < score: 
                best = score
                best_svm = svm 

        print "Best score: %s" % best
        f = open(args['backing_store'], 'wb')
        cPickle.dump((vec,transformer,svm),f)
        f.close()

    if path.isfile(args['backing_store']):        
        f = open(args['backing_store'], 'rb')
        (vec,transformer,svm) = cPickle.load(f)
        f.close()
    else: 
        sys.exit("Unable to load backing store")

    # This is just for the craic at this stage.
    if args['examine']: 
        # not yet implemented
        s = metadata.read_file(args['examine'])
        segments = metadata.chunkify(s)
        counts = vec.transform(segments) 
        tfidf = transformer.transform(counts) 
        
        results = svm.predict(tfidf.toarray())
        proba = None
        if 'predict_proba' in dir(svm): 
            proba = svm.predict_proba(tfidf.toarray())
        pos = filter(lambda x: x==1, results)
        neg = filter(lambda x: x==0, results)
        print "# pos: %s" % len(pos)
        print "# neg: %s" % len(neg)
        print "Segments classified: %s %%" % (len(pos) / float(len(results)) * 100)
        try: 
            if proba <> None: 
                no = [x for [x, y] in proba]
                yes = [y for [x, y] in proba]
                print "Mean probability of classifications:  No: %s Yes: %s" % (numpy.mean(no), numpy.mean(yes))
        except Exception as e: 
            print e



    