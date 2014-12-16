#!/usr/bin/env python
"""
Ideally we would use word vectors from a very large corpus of english words 
such as the one given by Google.

Currently simply reusing the corpus of segments.
"""
import argparse
from gensim.models import Word2Vec
from tokenise import Sentences
import logging
import metadata

__LOG_FORMAT__ = "%(asctime)-15s %(message)s"
__LOG_PATH__ = './joyce-predict.log'
if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='Train word embeddings')
    parser.add_argument('--log', help='Log file', default=__LOG_PATH__)
    parser.add_argument('--ngram-type', help='Either word or char n-gram', default='word')
    parser.add_argument('--file', help='File name of w2v backing store', default='words.w2v')
    args = vars(parser.parse_args())

    # set up logging
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.basicConfig(filename=args['log'],level=logging.INFO,
                        format=__LOG_FORMAT__)

    # fix chunking to respect sentence boundaries
    segments = metadata.get_training_segments()
    
    model = None
    for segment in segments: 
        if model: 
            model.train(Sentences(segment))
        else: 
            model = Word2Vec(Sentences(segment), size=100, window=5, min_count=5, workers=4)

    model.save(args['file'])
    
    
