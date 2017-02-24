#! /usr/bin/env python3

import os
import csv

from nameparser import HumanName
from pymarc import MARCReader
from titlecase import titlecase


def import_all_records(file):
    all_records = list()
    with open(file, 'rb') as f:
        reader = MARCReader(f)
        for record in reader:
            all_records.append(record)
    return all_records


def import_dup_uids(file):
    duplicate_uids = []
    with open(file, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            duplicate_uids.append(line.replace('.pdf', '').strip())
    return duplicate_uids


def make_set_of_restricteds():
    restricted_range_a = set(range(3048322, 3335145))
    restricted_range_b = {3021429, 3030348, 3451495}
    restricted_range_c = {3049191, 3049223, 3051440, 3053695, 3053696}
    restricted_range_d = set(range(3049188, 3329096))
    all_restricteds = set().union(restricted_range_a,
                                  restricted_range_b,
                                  restricted_range_c,
                                  restricted_range_d)
    all_restricteds.remove(3136164)
    return all_restricteds


def lookup_clean_title(record):
    wrong_roman_numeral = {' Ii': ' II',
                           ' Iii ': ' III ',
                           '-Iii': '-III',
                           ' Iii.': ' III.',
                           ' Iv ': ' IV ',
                           ' Vi ': ' VI ',
                           ' Iv.': ' IV.',
                           ' Iv)': 'IV)',
                           ' Viii': ' VIII',
                           '-Vii ': '-VII',
                           '-Viii': '-VIII',
                           ' Vii': ' VII',
                           }
    text = record.get_fields('245')[0].value()
    text = titlecase(text)
    text = text.replace(':  ', ": ")
    for k, v in wrong_roman_numeral.items():
        if k in text:
            text = text.replace(k, v)
    return text


def make_dropbox_url(record):
    uid = lookup_uid(record)
    url = 'some.dropbox.url/public/something/{}.pdf'.format(uid)
    return url


def interpret_directors(record):
    text_a, text_b = parse_500(record)
    return split_directors(text_b)


def parse_500(record):
    value_500 = [i.value() for i in record.get_fields('500')]
    if len(value_500) == 1:
        return value_500[0], ''
    else:
        return value_500[0], value_500[1]


def find_source(record):
    fields = [i.value() for i in record.get_fields('500') if 'Source' in i.value()][0]
    fields = unperiod(fields)
    fields = fields.replace('Source: ', '')
    return fields


def split_directors(text_b):
    directors_list = parse_advisors_field(text_b)
    if directors_list:
        if len(directors_list) == 3:
            return directors_list[0], directors_list[1], directors_list[2]
        elif len(directors_list) == 2:
            return directors_list[0], directors_list[1], ''
        elif len(directors_list) == 1:
            return directors_list[0], '', ''
    return ('', '', '')


def parse_advisors_field(text):
    for title in ('Directors: ',
                  'Director: ',
                  'Co-Chairs: ',
                  'Co-chairs: ',
                  'Co-Chairmen: ',
                  'Adviser: ',
                  'Advisers: ',
                  'Chair: ',
                  'Directed: '
                  ):
        if title in text:
            text = text.replace(title, '')
            text = text
            text = unperiod(text)
            if text:
                return [i.strip() for i in text.split('; ')]
    else:
        return ''


def unperiod(text):
    if text[-1] == '.':
        return text[:-1]
    return text


def combine_520(record):
    list_520 = [i for i in record.get_fields('520')]
    if list_520:
        combined_text = ' '.join([i.value() for i in list_520])
    else:
        combined_text = ''
    return combined_text


def combine_650(record):
    value_650 = [i.value() for i in record.get_fields('650')]
    value_650 = [i.capitalize().replace('.', '') for i in value_650]
    if value_650:
        combined_text = '; '.join(value_650)
    else:
        combined_text = ''
    return combined_text


def parse_author_names(record):
    name_clump = record.get_fields('100')[0].value()
    name_clump = unperiod(name_clump)
    name = HumanName(name_clump)
    last_name = name.last
    middle_name = name.middle
    suffix = name.suffix
    suffix = standardize_suffix(suffix)
    if name.nickname:
        first_name = "{} {}".format(name.first, name.nickname)
    else:
        first_name = name.first
    if "arch" in last_name.lower():
        print(name_clump)
    return titlecase(first_name), titlecase(middle_name), titlecase(last_name), suffix


def standardize_suffix(text):
    replace_dict = {'JR': 'Jr',
                    'SR': 'Sr',
                    '3RD': 'III',
                    'ED': 'Ed.'
                    }
    for wrong in replace_dict:
        if wrong in text:
            text = text.replace(wrong, replace_dict[wrong])
    return text


def lookup_inst(record):
    text = record.get_fields('710')[0].value()
    text = unperiod(text)
    return text


def lookup_isbn(record):
    if record.get_fields('020'):
        return record.get_fields('020')[0].value()
    return ''


def csv_writer(data, path):
    with open(path, "w", newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        for line in data:
            writer.writerow(line)


def build_csv(to_do_records):
    csv_data = []
    csvfieldnames = ['urn',
                     "title",
                     "fulltext_url",
                     'keywords',
                     'abstract',
                     "author1_fname",
                     'author1_mname',
                     'author1_lname',
                     'author1_suffix',
                     'author1_email',
                     'author1_institution',
                     'advisor1',
                     'advisor2',
                     'advisor3',
                     'disciplines',
                     'comments',
                     'degree_name',
                     'department',
                     "document_type",
                     'publication_date',
                     'season',
                     'release_date',
                     'ISBN',
                     'pagelength',
                     'source',
                     'diss_note',
                     'host_item',
                     'language',
                     'host_url',
                     ]
    csv_data.append(csvfieldnames)

    for record in to_do_records:
        csv_urn = lookup_uid(record)
        csv_title = lookup_clean_title(record)
        fulltext_url = make_dropbox_url(record)
        csv_keywords = combine_650(record)
        csv_abstract = combine_520(record)
        csv_first_name, csv_middle_name, csv_last_name, csv_suffix = parse_author_names(record)
        csv_author_email = ''
        csv_institution = lookup_inst(record)
        csv_advisor1, csv_advisor2, cvs_advisor3 = interpret_directors(record)
        csv_advisor3 = ''
        csv_disciplines = ''
        csv_comments = ''
        csv_degree_name = record.get_fields('791')[0].value()
        csv_department = ''
        csv_document_type = 'Thesis'
        csv_publication_date = record.get_fields('792')[0].value()
        csv_season = ''
        csv_release_date = ''
        csv_isbn = lookup_isbn(record)
        csv_pagelength = record.get_fields('300')[0].value().replace(' p.', '')
        csv_source = find_source(record)
        csv_diss_note = unperiod(record.get_fields('502')[0].value())
        csv_host_item = unperiod(record.get_fields('773')[0].value())
        csv_language = record.get_fields('793')[0].value()
        csv_host_url = record.get_fields('856')[0].value()

        csv_data.append([csv_urn,
                         csv_title,
                         fulltext_url,
                         csv_keywords,
                         csv_abstract,
                         csv_first_name,
                         csv_middle_name,
                         csv_last_name,
                         csv_suffix,
                         csv_author_email,
                         csv_institution,
                         csv_advisor1,
                         csv_advisor2,
                         csv_advisor3,
                         csv_disciplines,
                         csv_comments,
                         csv_degree_name,
                         csv_department,
                         csv_document_type,
                         csv_publication_date,
                         csv_season,
                         csv_release_date,
                         csv_isbn,
                         csv_pagelength,
                         csv_source,
                         csv_diss_note,
                         csv_host_item,
                         csv_language,
                         csv_host_url,
                         ])
    output_folder = '/home/francis/Desktop/lsu-git/Proquest_to_DigitalCommons/output'
    os.makedirs(output_folder, exist_ok=True)
    csv_writer(csv_data, '/home/francis/Desktop/lsu-git/Proquest_to_DigitalCommons/output/scrap_Proquest.csv')


def find_record(uid):
    for record in all_records:
        if lookup_uid(record) == uid:
            return record.as_dict()


def lookup_uid(record):
    return record.get_fields('001')[0].value().replace('AAI', '')


if __name__ == '__main__':
    all_records = import_all_records('source_data/MARCDATA.MRC')
    restricted_uids = make_set_of_restricteds()
    duplicate_uids = import_dup_uids('source_data/DuplicatedInDigitalCommons.txt')

    to_do_records = [i for i in all_records
                     if lookup_uid(i) not in restricted_uids and lookup_uid(i) not in duplicate_uids
                     ]
    build_csv(to_do_records)
