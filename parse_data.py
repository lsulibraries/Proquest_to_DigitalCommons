#! /usr/bin/env python3

from pymarc import MARCReader
import os


with open('source_data/MARCDATA.MRC', 'rb') as f:
    reader = MARCReader(f)
    all_records = list()
    for record in reader:
        all_records.append(record)

all_records[0].as_dict()


def lookup_uid(record):
    return record.get_fields('001')[0].value().replace('AAI', '')


print(lookup_uid(all_records[0]))


pdf_not_on_U = list()

for record in all_records:
    uid = lookup_uid(record)
    if os.path.isfile('/media/francis/U/ProquestDissertations/UnrestrictedTheses/{}.pdf'.format(uid)):
        continue
    pdf_not_on_U.append(uid)
