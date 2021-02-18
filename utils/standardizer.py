from datetime import datetime
from xylose.scielodocument import Citation
from utils.citation_utils import clean_author, clean_end_page, citation_id
from utils.field_processor import (
    preprocess_journal_title,
    preprocess_publication_date,
    preprocess_default,
    preprocess_issue,
    preprocess_volume
)
from utils.journal_standardizer import STATUS_NOT_NORMALIZED


class Standardizer:
    def __init__(self, journal_standardizer):
        self.jstd = journal_standardizer

    def standardize(self, citation: Citation, collection: str):
        cit_std = {'_id': citation_id(citation, collection),
                   'update-date': datetime.now()}

        if citation.publication_type == 'article':
            cit_std.update(self.standardize_article(citation))
        elif citation.publication_type == 'book':
            if citation.chapter_title:
                cit_std.update(self.standardize_chapter(citation))
            else:
                cit_std.update(self.standardize_book(citation))

        return cit_std

    def standardize_article(self, citation: Citation):
        return {
            'publication_type': 'article',
            'std_journal': self._standardize_journal(citation),
            'std_authors': self._standardize_authors(citation.authors),
            'std_publication_date': self._standardize_date(citation.publication_date),
            'std_title': self._standardize_title(citation.title()),
            'std_volume': self._standardize_volume(citation.volume),
            'std_pages': self._standardize_pages(citation.start_page, citation.end_page),
            'std_issue': self._standardize_issue(citation.issue)
        }

    def standardize_chapter(self, citation: Citation):
        return {
            'publication_type': 'chapter',
            'std_authors': self._standardize_authors(citation.authors),
            'std_title': self._standardize_title(citation.chapter_title),
            'std_book_authors': self._standardize_authors(citation.monographic_authors),
            'std_book_title': self._standardize_title(citation.title()),
            'std_date': self._standardize_date(citation.publication_date),
            'std_pages': self._standardize_pages(citation.start_page, citation.end_page),
            'std_publisher': self._standardize_publisher(citation.publisher),
            'std_publisher_address': self._standardize_publisher_address(citation.publisher_address)
        }

    def standardize_book(self, citation: Citation):
        return {
            'publication_type': 'book',
            'std_authors': self._standardize_authors(citation.authors),
            'std_date': self._standardize_date(citation.publication_date),
            'std_title': self._standardize_title(citation.title()),
            'std_publisher': self._standardize_publisher(citation.publisher),
            'std_publisher_address': self._standardize_publisher_address(citation.publisher_address)
        }

    def _standardize_journal(self, citation: Citation):
        cleaned_journal_title = preprocess_journal_title(citation.source, discard_invalid_chars=True, toggle_upper=True)
        std_journal = self.jstd.standardize_journal(citation, cleaned_journal_title, 'exact')

        if std_journal['status'] == STATUS_NOT_NORMALIZED:
            std_journal = self.jstd.standardize_journal(citation, cleaned_journal_title, 'fuzzy')

        std_journal['cited-journal-title'] = cleaned_journal_title

        return std_journal

    def _standardize_authors(self, authors):
        std_authors = []

        if authors:
            for a in authors:
                cleaned_author = clean_author(a)
                if cleaned_author:
                    std_authors.append(cleaned_author)

        return std_authors

    def _standardize_date(self, date):
        try:
            return preprocess_publication_date(date)
        except TypeError:
            return ''

    def _standardize_pages(self, first_page, end_page):
        pp_first_page = preprocess_default(first_page)
        pp_end_page = preprocess_default(end_page)

        cleaned_end_page = clean_end_page(pp_first_page, pp_end_page)

        pages = ''
        if pp_first_page and cleaned_end_page:
            pages = '-'.join([pp_first_page, cleaned_end_page])

        return {'first_page': pp_first_page,
                'end_page': cleaned_end_page,
                'pages': pages}

    def _standardize_volume(self, volume):
        return preprocess_volume(volume)

    def _standardize_issue(self, issue):
        return preprocess_issue(issue)

    def _standardize_title(self, title):
        return preprocess_default(title).lower()

    def _standardize_publisher(self, publisher):
        return preprocess_default(publisher).lower()

    def _standardize_publisher_address(self, publisher_address):
        return preprocess_default(publisher_address).lower()
