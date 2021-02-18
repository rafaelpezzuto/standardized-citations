import argparse
import logging
import os
import sys
sys.path.append('..')

from datetime import datetime, timedelta
from pymongo import MongoClient, uri_parser
from requests import ReadTimeout
from utils.journal_standardizer import JournalStandardizer
from utils.standardizer import Standardizer
from xylose.scielodocument import Article


LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', 'INFO')
JOURNAL_STANDARDIZER_PATH = os.environ.get('JOURNAL_STANDARDIZER_PATH', '/opt/data/bc-v1.bin')
MONGO_STD_CITATIONS_PERSIT_BUCKET_SIZE = int(os.environ.get('MONGO_DB_STD_CITATIONS_PERSIT_BUCKET_SIZE', '500'))
MONGO_URI_STD_CITATIONS = os.environ.get('MONGO_DB_STD_CITATIONS', 'mongodb://127.0.0.1:27017/scielo_search.std_citations')
MONGO_URI_ARTICLE_META = os.environ.get('MONGO_URI_ARTICLE_META', 'mongodb://127.0.0.1:27017/articlemeta.articles')


def mongo_collection(mongo_uri):
    puri = uri_parser.parse_uri(mongo_uri)

    database = puri['database']
    collection = puri['collection']

    return MongoClient(MONGO_URI_ARTICLE_META).get_database(database).get_collection(collection)


def persist_data(std_citations: list, mongo_uri_std_citations):
    logging.info('Persisting %d rows' % len(std_citations))
    mc_std_cits = mongo_collection(mongo_uri_std_citations)

    for s in std_citations:
        mc_std_cits.update({'_id': s['_id']},
                           s,
                           upsert=True)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-j', '--journal_standardizer_path',
        default=JOURNAL_STANDARDIZER_PATH
    )

    parser.add_argument(
        '-c', '--col',
        default=None,
        dest='collection',
        help='Standardize cited references in an entire collection'
    )

    parser.add_argument(
        '-f', '--from_date',
        default=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        help='Standardize cited references in documents published from a date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '-u', '--until_date',
        default=datetime.now().strftime('%Y-%m-%d'),
        help='standardize cited references in documents published until a date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '-x',
        dest='use_exact',
        action='store_true',
        default=False
    )

    parser.add_argument(
        '-z',
        dest='use_fuzzy',
        action='store_true',
        default=False
    )

    parser.add_argument(
        '--mongo_uri_std_citations',
        default=MONGO_URI_STD_CITATIONS
    )

    parser.add_argument(
        '--logging_level',
        default=LOGGING_LEVEL
    )

    params = parser.parse_args()

    logging.basicConfig(level=params.logging_level,
                        format='[%(asctime)s] %(levelname)s %(message)s',
                        datefmt='%d/%b/%Y %H:%M:%S')

    article_meta = mongo_collection(MONGO_URI_ARTICLE_META)

    logging.info('Creating JournalStandardizer')
    jstd = JournalStandardizer(params.journal_standardizer_path,
                               use_exact=params.use_exact,
                               use_fuzzy=params.use_fuzzy)
    standardizer = Standardizer(jstd)

    logging.info('Standardizing articles\' cited references for published articles between %s and %s'
                 % (params.from_date, params.until_date))

    std_citations = []

    from_date = datetime.strptime(params.from_date, '%Y-%m-%d')
    until_date = datetime.strptime(params.until_date, '%Y-%m-%d')

    try:
        for j in article_meta.find({'$and': [{'processing_date': {'$gte': from_date}},
                                             {'processing_date': {'$lte': until_date}}]},
                                   no_cursor_timeout=True):
            doc = Article(j)

            logging.debug('Standardizing %s' % doc.publisher_id)

            if doc.citations:
                for c in doc.citations:
                    cit_std = standardizer.standardize(c, doc.collection_acronym)
                    if len(cit_std.keys()) > 2:
                        std_citations.append(cit_std)

            if len(std_citations) >= MONGO_STD_CITATIONS_PERSIT_BUCKET_SIZE:
                persist_data(std_citations, params.mongo_uri_std_citations)
                std_citations = []

        if len(std_citations) > 0:
            persist_data(std_citations, params.mongo_uri_std_citations)

    except ReadTimeout:
        pass


if __name__ == '__main__':
    main()
