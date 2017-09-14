#!/usr/bin/python
# coding: utf-8
from publications_helpers import *
from pybtex.database import parse_file
from datetime import date
from unidecode import unidecode
import os
import jinja2
import datetime
import argparse
import subprocess
import json

now = datetime.datetime.now()

def create_publication_page(key, config, templateEnv, bibentry, paper):
    originalWD = os.getcwd()
    os.chdir(config["pub-data-directory"])

    base_filename = str(key)
    paper["current_year"] = now.year

    print u"Creating publication page for %s" % base_filename

    # Paper downloads
    Paper_downloads = []
    addBasicDownloads(Paper_downloads, "paper", config, base_filename)
    addDOILink(Paper_downloads, bibentry)
    paper["Paper_downloads"] = Paper_downloads

    # Custom extra paper downloads
    Extrapaper_downloads = []
    addExtraDownloads(Extrapaper_downloads, "paper", bibentry)
    paper["Extrapaper_downloads"] = Extrapaper_downloads

    # Slide downloads
    Slide_downloads = []
    addBasicDownloads(Slide_downloads, "slide", config, base_filename)
    paper["Slide_downloads"] = Slide_downloads

    # Custom extra paper downloads
    Extraslide_downloads = []
    addExtraDownloads(Extraslide_downloads, "slide", bibentry)
    paper["Extraslide_downloads"] = Extraslide_downloads
    paper["num_slides"] = len(Extraslide_downloads) + len(Slide_downloads)

    # Video downloads
    Video_downloads = []
    addBasicDownloads(Video_downloads, "video", config, base_filename)
    paper["Video_downloads"] = Video_downloads

    Youtube_downloads = []
    addYoutubeDownloads(Youtube_downloads, bibentry)
    paper["Youtube_downloads"] = Youtube_downloads
    paper["num_videos"] = len(Video_downloads) + len(Youtube_downloads)

    # Data downloads
    Data_downloads = []
    addExtraDownloads(Data_downloads, "data", bibentry)
    paper["Data_downloads"] = Data_downloads

    Code_downloads = []
    addExtraDownloads(Code_downloads, "code", bibentry)
    paper["Code_downloads"] = Code_downloads

    # Output the processed template.
    if 'extra-no-webpage' not in bibentry.fields:
        os.chdir(originalWD)

        path, page = os.path.split(config["pub-pages-template"])
        ipath = os.path.join(path, page + ".jnj")
        opath = os.path.join(config["pub-pages-output-directory"], base_filename + ".html")
        print "Creating " + page + ".html"
        print "Reading from: " + ipath
        print "Writing to: " + opath

        templateEnv.get_template(ipath).stream(paper).dump(opath)


def create_main(config, templateEnv, buildPublicationPages=False):
    # Load the list of publications from bib file
    bib_data = parse_file(config["bib-file"])
    bib_sorted = sorted(bib_data.entries.items(), cmp=sort_by_year)

    originalWD = os.getcwd()
    os.chdir(config["pub-data-directory"])

    # Create the Papers_years loop for chronological publication listing
    Papers_years = []
    paper_year_map = {}
    for key, bibentry in bib_sorted:
        year = bibentry.fields['year']
        if year not in paper_year_map and 'extra-omit-from-website' not in bibentry.fields and bibentry.type != 'patent':
            # insert the year into the Papers_years loop
            paper_year = {}
            paper_year["year"] = str(bibentry.fields['year'])
            paper_year["papers"] = []
            paper_year_map[year] = len(Papers_years)
            Papers_years.append(paper_year)

    total_citations = 0

    for key, bibentry in bib_sorted:
        base_filename = str(key)

        if 'extra-omit-from-website' in bibentry.fields:
            print u"Skipping %s" % base_filename
            continue

        # change months back to names
        month_names = {
            '1': 'January',
            '2': 'February',
            '3': 'March',
            '4': 'April',
            '5': 'May',
            '6': 'June',
            '7': 'July',
            '8': 'August',
            '9': 'September',
            '10': 'October',
            '11': 'November',
            '12': 'December'
        }
        if 'month' in bibentry.fields and bibentry.fields['month'] in month_names:
            bibentry.fields['month'] = month_names[bibentry.fields['month']]

        print u"Adding %s to publications index" % base_filename

        paper = {}
        paper["base_filename"] = base_filename
        paper["type"] = bibentry.type
        paper["title"] = latex_to_html(stripBraces(bibentry.fields['title']))
        paper["venue"] = getVenue(bibentry)

        # Setup the thumbnail and teaser image
        addTeaserAndThumbnail(paper, config, base_filename, bibentry)

        # Create the 'affiliations' loop.
        affiliations = []
        for affilnumber in range(1, 10):
            affilkey = "extra-affiliation-" + str(affilnumber)
            if affilkey in bibentry.fields:
                affiliations.append(latex_to_html(bibentry.fields[affilkey]))
        paper["affiliations"] = affiliations

        # Create the 'authors' loop.
        authors = []
        author_num = 0
        if 'author' in bibentry.persons:
            for person in bibentry.persons['author']:
                author_num += 1
                affilkey = 'extra-author-affiliation-' + str(author_num)
                affil = latex_to_html(bibentry.fields[affilkey]) if (affilkey in bibentry.fields) else "X"
                authors.append(addPerson(person, affil, affiliations, config["author-websites"]))
        paper["authors"] = authors

        # Create the 'editors' loop.
        editors = []
        if 'editor' in bibentry.persons:
            for person in bibentry.persons['editor']:
                editors.append(addPerson(person, "X", affiliations, config["author-websites"]))
        paper["editors"] = editors

        # copy fields from bib entry to jinja
        for field in ['number', 'volume', 'pages', 'month', 'year', 'abstract']:
            if field in bibentry.fields:
                paper[field] = latex_to_html(bibentry.fields[field])
        for field in ['select', 'accolades', 'copyright', 'caption']:
            extrafield = 'extra-' + field
            if extrafield in bibentry.fields:
                paper[field] = latex_to_html(bibentry.fields[extrafield])

        # Create the 'links' loop.
        links = []
        addProjectURL(paper, base_filename, bibentry)
        addBasicDownloads(links, "paper", config, base_filename, True)
        addBasicDownloads(links, "slide", config, base_filename, True)
        addDOILink(links, bibentry)
        paper["quicklinks"] = links

        paper["bibcitation"] = writeEntryAsBibTex(bibentry, key)

        if 'extra-scholar-count' in bibentry.fields:
            scholar_citations = {}
            scholar_citations["count"] = int(bibentry.fields['extra-scholar-count'])
            scholar_citations["url"] = latex_to_unicode(bibentry.fields['extra-scholar-url'])
            paper["scholar_citations"] = scholar_citations
            total_citations += scholar_citations["count"]

        Papers_years[paper_year_map[bibentry.fields['year']]]["papers"].append(paper)

        if buildPublicationPages:
            os.chdir(originalWD)
            create_publication_page(
                key, config, templateEnv, bibentry, paper)
            os.chdir(originalWD)
            os.chdir(config["pub-data-directory"])

    tparams = {}
    tparams["current_year"] = now.year
    tparams["years"] = Papers_years
    tparams["total_citations"] = total_citations
    print "Total citation count: %d" % total_citations

    tparams["first_collaborator_year"] = now.year - 2
    collaborators3 = extractCoAuthors(
        bib_sorted, range(now.year - 2, now.year + 1))
    collaborators4 = extractCoAuthors(
        bib_sorted, range(now.year - 3, now.year - 2))

    tparams["collaborators_three_years"] = formatCoAuthors(
        collaborators3, config["author-websites"])
    tparams["collaborators_fourth_year"] = formatCoAuthors(
        collaborators4 - collaborators3, config["author-websites"])

    os.chdir(originalWD)

    path, page = os.path.split(config["pub-index-template"])
    ipath = os.path.join(path, page + ".jnj")
    opath = os.path.join(config["pub-index-output-directory"], page + ".html")
    print "Creating " + page + ".html"
    print "Reading from: " + ipath
    print "Writing to: " + opath

    templateEnv.get_template(ipath).stream(tparams).dump(opath)


def create_static_pages(config, templateEnv):
    tparams = {}
    tparams["current_year"] = now.year

    for page in config["static-page-templates"]:
        ipath = page + ".jnj"
        opath = os.path.join(config["static-page-output-root"], page + ".html")
        print "Creating " + page + ".html"
        print "Reading from: " + ipath
        print "Writing to: " + opath
        templateEnv.get_template(ipath).stream(tparams).dump(opath)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Build the website from jnj and bib source files.')
    parser.add_argument('-i', '--build-pub-index', type=bool, nargs='?', default=False, const=True,
                        help='set to True to build the main page and publications index from the bib file.')
    parser.add_argument('-p', '--build-pub-pages', type=bool, nargs='?', default=False, const=True,
                        help='set to True to build the individual publications pages from the bib file.')

    args = parser.parse_args()
    print 'Building (publication) index: %s' % args.build_pub_index
    print 'Building publication pages: %s' % args.build_pub_pages

    config = json.load(open('config.json'))

    # very basic input validation
    if "bib-file" not in config or \
       "jnj-templates-root" not in config or \
       "pub-index-template" not in config or \
       "pub-index-output-directory" not in config or \
       "pub-pages-template" not in config or \
       "pub-pages-output-directory" not in config or \
       "pub-data-directory" not in config or \
       "static-page-templates" not in config or \
       "static-page-output-root" not in config or \
       "author-websites" not in config:
        raise SyntaxError("Missing data in build.json!")

    # Create the jinja2 environment.
    # Notice the use of trim_blocks, which greatly helps control whitespace.
    templateLoader = jinja2.FileSystemLoader(searchpath=config["jnj-templates-root"])
    templateEnv = jinja2.Environment(loader=templateLoader, trim_blocks=True, lstrip_blocks=True)

    create_static_pages(config, templateEnv)
    if args.build_pub_index:
        create_main(config, templateEnv, args.build_pub_pages)
