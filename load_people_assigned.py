""" Main program that loads related people from a file

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-21
:Copyright: 2018, Arthur Goldberg
:License: MIT
"""

import sys
import argparse
import logging
import related_person
from related_person import Gender, RelatedPerson, RelatedPersonError


class RawPersonRecord(object):
    FIELDS = 5

    def __init__(self, id, name, father_id, mother_id, gender, row):
        self.id = id
        self.name = name
        self.father_id = father_id
        self.mother_id = mother_id
        self.gender = gender
        self.row = row

    @staticmethod
    def make_from_line(line, row):
        l = line.strip().split('\t')
        if len(l) != RawPersonRecord.FIELDS:
            raise ValueError("row {}: has {} fields, not {}".format(row, len(l), RawPersonRecord.FIELDS))
        t = tuple(l + [row])
        return RawPersonRecord(*t)


class LoadPeople(object):
    NULL_ID = '0'

    def __init__(self):
        self.buffer = []
        self.people_index = {}

    @staticmethod
    def all_people(people_index):
        for id in sorted(people_index.keys()):
            print(str(people_index[id]))

    # todo: write phase1
    def phase1(self):
        # Phase 1:

        parser = argparse.ArgumentParser()
        parser.add_argument("infile", type=argparse.FileType('r'))
        parser.add_argument("--outfile", '-o', type=argparse.FileType('a+'))
        print(parser.parse_args())
        return parser.parse_args()

    def phase2(self):
        # Phase 2:
        row = 0
        errors = []
        bad_ids = set()
        # todo: report failure to open and quit, or have file opened by command line parsing
        args = self.phase1()
        filename = args.infile

        with filename as f:
            for line in f:
                row += 1
                try:
                    self.buffer.append(RawPersonRecord.make_from_line(line, row))
                except ValueError as e:
                    errors.append(str(e))

        # check IDs, genders, & create RelatedPersons
        for raw_person in self.buffer:
            try:
                # check for dupes
                if raw_person.id in self.people_index:
                    bad_ids.add(raw_person.id)
                    del self.people_index[raw_person.id]
                if raw_person.id in bad_ids:
                    raise RelatedPersonError("duplicate ID: {}".format(raw_person.id))

                # todo: get and check gender
                gender = Gender.get_gender(raw_person.gender)

                # make RelatedPerson
                related_person = RelatedPerson(raw_person.id, raw_person.name, gender)
                self.people_index[raw_person.id] = related_person
            except RelatedPersonError as e:
                errors.append("row {}: {}".format(raw_person.row, str(e)))
                bad_ids.add(raw_person.id)

        if errors:
            # todo: write to output determined by command line input
            text_1 = '\n- individual errors -'
            text_2 = '\n'.join(errors)
            if args.outfile:
                with args.outfile as o:
                    o.write(text_1 + text_2)
            else:
                print(text_1, text_2)

    def check_parent(self, raw_person, parent):
        if parent == 'mother':
            if raw_person.mother_id != LoadPeople.NULL_ID:
                if raw_person.mother_id not in self.people_index:
                    raise RelatedPersonError("{} missing mother {}".format(raw_person.id, raw_person.mother_id))
        elif parent == 'father':
            if raw_person.father_id != LoadPeople.NULL_ID:
                if raw_person.father_id not in self.people_index:
                    raise RelatedPersonError("{} missing father {}".format(raw_person.id, raw_person.father_id))

    def set_parent(self, raw_person, parent):
        related_person = self.people_index[raw_person.id]
        if parent == 'mother':
            if raw_person.mother_id != LoadPeople.NULL_ID:
                mother = self.people_index[raw_person.mother_id]
                related_person.set_mother(mother)
        elif parent == 'father':
            if raw_person.father_id != LoadPeople.NULL_ID:
                father = self.people_index[raw_person.father_id]
                related_person.set_father(father)

    def phase3(self):
        # Phase 3:
        errors = []
        bad_ids = set()
        args = self.phase1()

        for raw_person in self.buffer:
            if raw_person.id in self.people_index:

                # todo: check that the parents of raw_person exist; use check_parent() to help
                # set parents, which checks their gender
                if raw_person.id not in bad_ids:
                    for parent in ['mother', 'father']:
                        try:
                            self.check_parent(raw_person, parent)
                            self.set_parent(raw_person, parent)
                        except RelatedPersonError as e:
                            errors.append("row {}: for {} {}".format(raw_person.row, raw_person.id, str(e)))
                            bad_ids.add(raw_person.id)

        # delete all the RelatedPerson entries for the bad people
        for bad_id in bad_ids:
            del self.people_index[bad_id]

        # todo: create a log entry for each RelatedPerson that is verified

        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        for id in self.people_index:
            logging.info('ID:{} is successfully loaded.'.format(id), self.people_index[id])

        if errors:
            # todo: write to output determined by command line input
            text_1 = '\n- relatedness errors -'
            text_2 = '\n'.join(errors)
            if args.outfile:
                with args.outfile as o:
                    o.write(text_1 + text_2)
            else:
                print(text_1, text_2)

    def main(self):
        self.phase2()
        self.phase3()
        return self.people_index


# todo: use the input specified by the CLI
# Use command line such as python load_people_assigned.py test_bad.tsv -o output_error.txt
LoadPeople().main()
