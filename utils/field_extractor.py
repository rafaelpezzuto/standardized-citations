import html

from xylose.scielodocument import Citation, Article
from utils.field_processor import (
    clean_first_author,
    clean_publication_date,
    clean_journal_title,
    clean_field, preprocess_doi, preprocess_author_name, preprocess_journal_title
)


def extract_attrs_for_crossref(article: Article):
    cit_id_to_attrs = {}

    if article.citations:
        for cit in article.citations:
            if cit.publication_type == 'article':
                cit_id = extract_cit_id(cit, article.collection_acronym)
                cit_attrs = _extract_cit_attrs_for_crossref(cit)

                if cit_attrs:
                    cit_id_to_attrs[cit_id] = cit_attrs

    return cit_id_to_attrs


def _extract_cit_attrs_for_crossref(cit: Citation):
    if cit.doi:
        valid_doi = preprocess_doi(cit.doi)
        if valid_doi:
            return {'doi': valid_doi}

    attrs = {}

    if cit.first_author:
        first_author_surname = cit.first_author.get('surname', '')
        cleaned_author_surname = preprocess_author_name(first_author_surname)
        if cleaned_author_surname:
            attrs.update({'aulast': cleaned_author_surname})

    journal_title = cit.source
    if journal_title:
        cleaned_journal_title = preprocess_journal_title(journal_title)
        if cleaned_journal_title:
            attrs.update({'title': cleaned_journal_title})

    publication_date = html.unescape(cit.publication_date) if cit.publication_date else None
    if publication_date and len(publication_date) >= 4:
        publication_year = publication_date[:4]
        if publication_year.isdigit():
            attrs.update({'data': publication_year})

    volume = html.unescape(cit.volume) if cit.volume else None
    if volume:
        attrs.update({'volume': volume})

    issue = html.unescape(cit.issue) if cit.issue else None
    if issue:
        attrs.update({'issue': issue})

    first_page = html.unescape(cit.first_page) if cit.first_page else None
    if first_page:
        attrs.update({'spage': first_page})

    if attrs:
        return attrs


def _extract_cit_authors(citation: Citation):
    c_authors = {}

    if citation.publication_type == 'article' or not citation.chapter_title:
        cleaned_first_author = clean_first_author(citation.first_author)
        if cleaned_first_author:
            c_authors['cleaned_first_author'] = cleaned_first_author
    else:
        if citation.analytic_authors:
            cleaned_chapter_first_author = clean_first_author(citation.analytic_authors[0])
            if cleaned_chapter_first_author:
                c_authors['cleaned_chapter_first_author'] = cleaned_chapter_first_author

            if citation.monographic_authors:
                cleaned_first_author = clean_first_author(citation.monographic_authors[0])
                if cleaned_first_author:
                    c_authors['cleaned_first_author'] = cleaned_first_author

    return c_authors


def extract_cit_data(citation: Citation, cit_standardized_data=None):
    """
    Extrai os dados de uma citação.

    :param citation: Citação da qual os dados serao extraidos
    :param cit_standardized_data: Caso seja artigo, usa o padronizador de título de periódico
    :return: Dicionário composto pelos pares de nomes dos ampos limpos das citações e respectivos valores
    """
    c_attrs = {}

    c_attrs.update(_extract_cit_authors(citation))

    cleaned_publication_date = clean_publication_date(citation.publication_date)
    if cleaned_publication_date:
        c_attrs['cleaned_publication_date'] = cleaned_publication_date

    if citation.publication_type == 'article':
        c_attrs.update(_extract_cit_fields_by_list(citation, ['issue', 'start_page', 'volume']))

        cleaned_journal_title = ''
        if cit_standardized_data:
            cleaned_journal_title = cit_standardized_data['official-journal-title'][0].lower()
            if cleaned_journal_title:
                c_attrs['cleaned_journal_title'] = cleaned_journal_title

        if not cleaned_journal_title:
            cleaned_journal_title = clean_journal_title(citation.source)
            if cleaned_journal_title:
                c_attrs['cleaned_journal_title'] = cleaned_journal_title

        cleaned_title = clean_field(citation.title())
        if cleaned_title:
            c_attrs['cleaned_title'] = cleaned_title

    elif citation.publication_type == 'book':
        c_attrs.update(_extract_cit_fields_by_list(citation, ['source', 'publisher', 'publisher_address']))

        cleaned_chapter_title = clean_field(citation.chapter_title)
        if cleaned_chapter_title:
            c_attrs['cleaned_chapter_title'] = cleaned_chapter_title

    return c_attrs


def _extract_cit_fields_by_list(citation: Citation, fields):
    """
    Extrai de uma citação os campos indicados na variável fields.

    :param citation: Citação da qual serão extraídos os campos
    :param fields: Campos a serem extraídos
    :return: Dicionário composto pelos pares campo: valor do campo
    """
    c_fields = {}

    for f in fields:
        cleaned_v = clean_field(getattr(citation, f))
        if cleaned_v:
            c_fields['cleaned_' + f] = cleaned_v

    return c_fields


def extract_cit_ids_keys(document: Article, standardizer):
    """
    Extrai as quadras (id de citação, pares de campos de citação, hash da citação, base) para todos as citações.
    São contemplados livros, capítulos de livros e artigos.

    :param document: Documento do qual a lista de citações será convertida para hash
    :param standardizer: Normalizador de título de periódico citado
    :return: Quadra composta por id de citação, dicionário de nomes de campos e valores, hash de citação e base
    """
    citations_ids_keys = []

    if document.citations:
        for cit in [c for c in document.citations if c.publication_type in citation_types]:
            cit_full_id = extract_cit_id(cit, document.collection_acronym)

            if cit.publication_type == 'article':
                cit_standardized_data = standardizer.find_one({'_id': cit_full_id, 'status': {'$gt': 0}})
                cit_data = extract_cit_data(cit, cit_standardized_data)

                for extra_key in ['volume', 'start_page', 'issue']:
                    keys_i = ARTICLE_KEYS + ['cleaned_' + extra_key]

                    article_hash_i = hash_keys(cit_data, keys_i)
                    if article_hash_i:
                        citations_ids_keys.append((cit_full_id,
                                                   {k: cit_data[k] for k in keys_i if k in cit_data},
                                                   article_hash_i,
                                                   'article_' + extra_key))

            else:
                cit_data = extract_cit_data(cit)

                book_hash = hash_keys(cit_data, BOOK_KEYS)
                if book_hash:
                    citations_ids_keys.append((cit_full_id,
                                               {k: cit_data[k] for k in BOOK_KEYS if k in cit_data},
                                               book_hash,
                                               'book'))

                    chapter_keys = BOOK_KEYS + ['cleaned_chapter_title', 'cleaned_chapter_first_author']

                    chapter_hash = hash_keys(cit_data, chapter_keys)
                    if chapter_hash:
                        citations_ids_keys.append((cit_full_id,
                                                   {k: cit_data[k] for k in chapter_keys if k in cit_data},
                                                   chapter_hash,
                                                   'chapter'))

    return citations_ids_keys


def extract_cit_id(citation: Citation, collection_acronym):
    """
    Monta o id completo de uma citação.

    :param citation: Citação da qual o id completo sera montado
    :param collection_acronym: Acrônimo da coleção SciELO na qual a citação foi referida
    :return: ID completo da citação formada pelo PID do documento citante, numero da citação e coleção citante
    """
    cit_id = citation.data['v880'][0]['_']
    return '{0}-{1}'.format(cit_id, collection_acronym)
