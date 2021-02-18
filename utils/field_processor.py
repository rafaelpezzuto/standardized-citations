import html
import re

from utils.string_processor import remove_double_spaces, alpha_num_space, remove_accents, remove_invalid_chars


PATTERN_PARENTHESIS = re.compile(r'[-a-zA-ZÀ-ÖØ-öø-ÿ|0-9]*\([-a-zA-ZÀ-ÖØ-öø-ÿ|\W|0-9]*\)[-a-zA-ZÀ-ÖØ-öø-ÿ|0-9]*', re.UNICODE)
PATTERN_DOI = re.compile(r'\d{2}\.\d+/.*$')
PATTERN_YEAR = re.compile(r'\d{4}')
PATTERN_ISSUE = re.compile(r'\d+')
PATTERN_VOLUME = re.compile(r'\d+')
SPECIAL_WORDS = ['IMPRESSO', 'IMPRESS', 'PRINTED', 'ONLINE', 'CDROM', 'PRINT', 'ELECTRONIC', 'ELETRONICO']


def preprocess_publication_date(text):
    matched_year = re.search(PATTERN_YEAR, text)
    if matched_year:
        return matched_year.group()
    return ''


def preprocess_default(text):
    """
    Aplica:
        1. Remoçao de acentos
        2. Manutençao de alpha e espaco
        3. Remoçao de espaços duplos
    Procedimento que faz tratamento padrao de limpeza
    :param text: string a ser tratada
    :return: string tratada
    """
    if text:
        return remove_double_spaces(alpha_num_space(remove_accents(text)))
    return ''


def preprocess_issue(text):
    text_dp = preprocess_default(text)

    first_matched_issue = re.search(PATTERN_ISSUE, text_dp)
    if first_matched_issue:
        return first_matched_issue.group(0)


def preprocess_volume(text):
    text_dp = preprocess_default(text)

    first_matched_vol = re.search(PATTERN_VOLUME, text_dp)
    if first_matched_vol:
        return first_matched_vol.group(0)

    return ''


def preprocess_doi(text):
    """
    Procedimento que trata DOI.

    :param text: caracteres que representam um código DOI
    :return: código DOI tratado
    """
    doi = PATTERN_DOI.findall(text)
    if len(doi) == 1:
        return doi[0]


def preprocess_journal_title(text, discard_invalid_chars=False, toggle_upper=False):
    text = html.unescape(text)

    if discard_invalid_chars:
        text = remove_invalid_chars(text)

    parenthesis_search = re.search(PATTERN_PARENTHESIS, text)
    while parenthesis_search is not None:
        text = text[:parenthesis_search.start()] + text[parenthesis_search.end():]
        parenthesis_search = re.search(PATTERN_PARENTHESIS, text)

    for sw in SPECIAL_WORDS:
        text = text.replace(sw, '')
    cleaned_text = remove_double_spaces(alpha_num_space(remove_accents(text), include_special_chars=True))

    if toggle_upper:
        return cleaned_text.upper()

    return cleaned_text.lower()
