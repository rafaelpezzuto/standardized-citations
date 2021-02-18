from xylose.scielodocument import Citation
from utils.field_processor import preprocess_default


def citation_id(citation: Citation, collection_acronym):
    cid = citation.data['v880'][0]['_']
    return '{0}-{1}'.format(cid, collection_acronym)


def clean_author(author):
    c_author = ''

    if author:
        initial = ''
        lastname = ''

        fa_surname = preprocess_default(author.get('surname', ''))
        fa_givennames = preprocess_default(author.get('given_names', ''))

        if fa_surname:
            lastname = fa_surname.split(' ')[-1]

        if fa_givennames:
            initial = fa_givennames[0]

        c_author = ' '.join([initial, lastname]).strip()

    return c_author.lower()


def clean_end_page(first_page: str, end_page: str):
    diff_len_pages = len(first_page) - len(end_page)

    if diff_len_pages > 0:
        return ''.join([first_page[:diff_len_pages]] + [end_page])
    else:
        return preprocess_default(end_page)
