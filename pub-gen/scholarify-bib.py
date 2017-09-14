#!/usr/bin/python
# coding: utf-8
from scholar import *
import pybtex.database.input.bibtex
import pybtex.database.output.bibtex
from unidecode import unidecode
from publications_helpers import personName, stripBraces
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a bib file and optionally add scholar citation counts.')
    parser.add_argument('-s', '--add-scholar',
                        help='set to True to query Google scholar and add citation statistics to the output bib file.',
                        action="store_true")

    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input bib file")
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output bib file")

    args = parser.parse_args()
    print 'Including Google scholar citation stats: %s' % args.add_scholar
    print 'Reading from: %s' % args.infile
    print 'Writing to: %s' % args.outfile

    month_names = {
        'jan': '1',
        'feb': '2',
        'mar': '3',
        'apr': '4',
        'may': '5',
        'jun': '6',
        'jul': '7',
        'aug': '8',
        'sep': '9',
        'oct': '10',
        'nov': '11',
        'dec': '12'
    }

    # Load the list of publications from bib file
    parser = pybtex.database.input.bibtex.Parser(encoding="UTF-8", macros=month_names)
    bib_data = parser.parse_file(getattr(args.infile, 'name', None))

    querier = ScholarQuerier()
    settings = ScholarSettings()
    querier.apply_settings(settings)
    total_citations = 0

    for key, bibentry in bib_data.entries.items():
        if args.add_scholar and bibentry.type != 'patent':
            query = SearchScholarQuery()
            authors_string = ""
            if 'author' in bibentry.persons:
                authors_string = unidecode(u' '.join([personName(author) for author in bibentry.persons['author'][:2]]))
            elif 'editor' in bibentry.persons:
                authors_string = unidecode(u' '.join([personName(editor) for editor in bibentry.persons['editor'][:2]]))

            title_string = stripBraces(bibentry.fields['title'])
            query.set_author(authors_string)
            query.set_phrase(title_string)
            query.set_num_page_results(1)
            query.set_timeframe(bibentry.fields['year'])
            query.set_scope(title_only=True)

            print "Checking Google scholar for: \"%s\", by %s" % (title_string, authors_string)

            querier.send_query(query)
            articles = querier.articles

            if (len(articles) > 0 and articles[0]['url_citations'] and articles[0]['num_citations'] > 0):
                bibentry.fields['extra-scholar-count'] = str(articles[0]['num_citations'])
                bibentry.fields['extra-scholar-url'] = articles[0]['url_citations']
                total_citations += articles[0]['num_citations']
                print "   Found: %d citations." % articles[0]['num_citations']
                # print "   scholar url: %s" % articles[0]['url_citations']
            else:
                print "   Found: 0 citations."

    print "Total citation count: %d" % total_citations

    writer = pybtex.database.output.bibtex.Writer(encoding="UTF-8")
    writer.write_file(bib_data, getattr(args.outfile, 'name', None))
