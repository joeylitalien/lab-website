#!/usr/bin/python
# coding: utf-8
# Helper functions for formatting publications page

import os
import re
import cgi
import json
from PIL import Image
from collections import OrderedDict
from pybtex.database import BibliographyData, Entry, parse_file
import pybtex.database.output.bibtex
import calendar
monthToInt = {name: num for num, name in enumerate(calendar.month_name) if num}

def customAlphaSort(list):
    # this function is needed only to ensure that a file like 'paper.pdf' appears before 'paper-supplemental.pdf'
    # all I really wanted to do was swap the lexographical order of '.' and '-'.
    # There might be a better way.
    alphabet = " .-+()[]0123456789_AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz"
    return sorted(list, key=lambda word: [alphabet.index(c) for c in word])

def sort_by_year(y, x):
    if int(x[1].fields['year']) != int(y[1].fields['year']):
        return int(x[1].fields['year']) - int(y[1].fields['year'])
    else:
        mx = 0
        my = 0
        if 'month' in x[1].fields:
            mx = monthToInt[x[1].fields['month']]
        if 'month' in y[1].fields:
            my = monthToInt[y[1].fields['month']]

        return mx - my


def stripBraces(str):
    return str.replace("{", u'').replace("}", u'')


def latex_to_unicode(str):
    import latexcodec
    return str.decode("ulatex+utf8")


def unicode_to_html(str):
    return str.encode('ascii', 'xmlcharrefreplace')


def latex_to_html(str):
    return unicode_to_html(latex_to_unicode(str))


def personName(person):
    name = ' '.join(person.first_names + person.middle_names + person.prelast_names + person.last_names + person.lineage_names)
    name = latex_to_unicode(name)
    return name


def addPerson(person, affiliation, affiliations, author_websites):
    author = {}
    author["name"] = personName(person)
    if author["name"] in author_websites:
        author["url"] = author_websites[author["name"]]
    if affiliation == "X":
        author["affiliation"] = "None"
        return author
    tokens = map(int, affiliation.split(","))
    affil = ", ".join([affiliations[t-1] for t in tokens])
    author["affiliation"] = affil
    return author


def extractCoAuthors(bib_sorted, year_range):
    coAuthorSet = {}
    gen = ((key, bibentry) for key, bibentry in bib_sorted if "extra-noconflicts" not in bibentry.fields and bibentry.type != "patent")
    for key, bibentry in gen:
        if bibentry.fields[u'year'] not in coAuthorSet:
            coAuthorSet[bibentry.fields[u'year']] = set()
        if 'author' in bibentry.persons:
            for author in bibentry.persons['author']:
                coAuthorSet[bibentry.fields[u'year']].add(personName(author))

    myset = set()
    for year in year_range:
        if str(year) in coAuthorSet:
            myset |= coAuthorSet[str(year)]

    return myset


def formatCoAuthors(coAuthorsSet, author_websites):
    collaborators = []
    for name in sorted(coAuthorsSet):
        if name == u"Wojciech Jarosz":
            continue
        if name in author_websites:
            collaborators.append(u"""<a href="%s">%s</a>""" % (author_websites[name], name))
        else:
            collaborators.append(name)

    return collaborators


def writeEntryAsBibTex(entry, key):
    # remove the abstract and "extra" fields, but preserve field order
    newfields = OrderedDict((key, latex_to_unicode(value)) for key, value in entry.fields.items() if "extra" not in key and key != "abstract")

    writer = pybtex.database.output.bibtex.Writer(encoding="utf-8")
    return writer.to_string(BibliographyData(entries={key: Entry(type_=entry.type, fields=newfields, persons=entry.persons)}))

def size_to_string(size):
    if size < 1024:
        return u'%dB' % size
    elif size < 1024 * 1024:
        return u'%dKB' % (size * .0009765625)
    elif size < 1024 * 1024 * 1024:
        return u'%dMB' % (size * .0009765625 * .0009765625)
    elif size < 1024 * 1024 * 1024 * 1024:
        return u'%dGB' % (size * .0009765625 * .0009765625 * .0009765625)


def addTeaserAndThumbnail(paper, json_data, base_filename, bibentry):
    # Find the thumbnail and teaser images
    m = re.compile(base_filename + json_data["regular-expressions"]["teaser"])
    for filename in customAlphaSort(os.listdir('../publications/images/')):
        g = m.search(filename)
        if g:
            paper["teaser_image"] = '../publications/images/' + filename

    m = re.compile(base_filename + json_data["regular-expressions"]["thumbnail"])
    for filename in customAlphaSort(os.listdir('../publications/images/')):
        g = m.search(filename)
        if g:
            paper["thumbnail"] = 'publications/images/' + filename

    teaser_width = "900"
    if 'extra-caption-width' in bibentry.fields:
        teaser_width = str(bibentry.fields['extra-caption-width'])
    elif "teaser_image" in paper:
        try:
            img = Image.open(paper["teaser_image"])
            # get the image's width and height in pixels
            width, height = img.size
            teaser_width = str(width)
        except:
            # filename not an image file
            print u"Error reading teaser image: %s" % paper["teaser_image"]

    paper["teaser_width"] = teaser_width


def addProjectURL(paper, base_filename, bibentry):
    if bibentry.type == 'patent':
        paper["url"] = cgi.escape(bibentry.fields['url'], quote=True)
        paper["external"] = True
    elif 'extra-webpage' in bibentry.fields:
        paper["url"] = cgi.escape(bibentry.fields['extra-webpage'], quote=True)
        paper["external"] = 'http://' in bibentry.fields['extra-webpage'] or 'https://' in bibentry.fields['extra-webpage']
    elif 'extra-no-webpage' not in bibentry.fields:
        paper["url"] = u'%s.html' % base_filename


def getVenue(bibentry):
    if bibentry.type == 'article':
        return latex_to_unicode(stripBraces(bibentry.fields['journal']))
    elif bibentry.type == 'inproceedings':
        return latex_to_unicode(stripBraces(bibentry.fields['booktitle']))
    elif bibentry.type == 'proceedings':
        return latex_to_unicode(stripBraces(bibentry.fields['series']))
    elif bibentry.type == 'phdthesis':
        return u'Ph.D. Dissertation, %s' % latex_to_unicode(bibentry.fields['school'])
    elif bibentry.type == 'thesis':
        return u'%s, %s' % (latex_to_unicode(bibentry.fields['type']), latex_to_unicode(bibentry.fields['school']))
    elif bibentry.type == 'techreport':
        return u'Tech. Report, %s' % latex_to_unicode(bibentry.fields['institution'])
    elif bibentry.type == 'patent':
        return u'Patent, %s %s' % (latex_to_unicode(bibentry.fields['location']), latex_to_unicode(bibentry.fields['number']))
    elif bibentry.type == 'misc':
        return latex_to_unicode(stripBraces(bibentry.fields['howpublished']))


def addBasicDownloads(links, dtype, json_data, base_filename, quick=False):
    m = re.compile(base_filename + json_data["regular-expressions"][dtype])
    for filename in customAlphaSort(os.listdir('./')):
        g = m.search(filename)
        if g:
            suffix = g.group(1)
            num = g.group(2)
            ext = g.group(3)
            if not quick or ("-small" not in suffix and "-fast-forward" not in suffix and ext not in ['mov', 'mp4', 'm4v', 'webm']):
                links.append(basicDownload(dtype, filename, json_data, num, suffix, ext))


def basicDownload(dtype, filename, json_data, num, suffix, ext):
    type_short = json_data[dtype + "-suffix-descriptions"][suffix]["short"]
    type_long = json_data[dtype + "-suffix-descriptions"][suffix]["long"]
    if num != '':
        type_long += u' ' + num
        type_short += u' ' + num

    link = {}
    link["type"] = ext
    link["url"] = filename
    link["text_short"] = u'%s (%s .%s)' % (type_short, size_to_string(os.path.getsize(filename)), ext)
    link["text_long"] = u'%s &middot; %s (%s)' % (type_long, json_data["extension-descriptions"][ext], size_to_string(os.path.getsize(filename)))
    return link


def addDOILink(links, bibentry):
    # add ACM Author-Izer link if it exists
    if 'extra-acm-author-izer' in bibentry.fields:
        id = cgi.escape(bibentry.fields['extra-acm-author-izer'], quote=True)
        link = {}
        link["type"] = u'acm'
        link["url"] = u'https://dl.acm.org/authorize?%s' % id
        link["external"] = True
        link["text_long"] = u'Official ACM Author-Izer version'
        link["text_short"] = u'publisher&#8217;s version'
        links.append(link)
    # otherwise add official publisher's page from DOI link
    elif 'doi' in bibentry.fields:
        url = cgi.escape(bibentry.fields['doi'], quote=True)
        link = {}
        link["type"] = u'doi-link'
        link["url"] = u'http://dx.doi.org/%s' % url
        link["external"] = True
        link["text_long"] = u'Publisher&#8217;s official version (may require a subscription)'
        link["text_short"] = u'Publisher&#8217;s version'
        links.append(link)


def addExtraDownloads(links, type, bibentry):
    for datanumber in range(1, 20):
        key = "extra-" + type + "-download-" + str(datanumber)
        if key in bibentry.fields:
            link = {}
            link["link"] = latex_to_html(bibentry.fields[key])
            link["external"] = 'http://' in bibentry.fields[key] or 'https://' in bibentry.fields[key]

            # set the link type using either the explicit bib field, or leave as default for type
            typekey = "extra-" + type + "-download-" + str(datanumber) + "-type"
            if typekey in bibentry.fields:
                link["type"] = bibentry.fields[typekey]
            else:
                link["type"] = type
            links.append(link)


def addYoutubeDownloads(links, bibentry):
    for videonumber in range(1, 20):
        key = "extra-youtube-download-" + str(videonumber)
        if key in bibentry.fields:
            link = {}
            link["text_long"] = u'Youtube video %s' % str(videonumber)
            link["text_short"] = u'Youtube video %s' % str(videonumber)
            link["url"] = u'http://www.youtube.com/watch?v=%s' % bibentry.fields[key]
            link["type"] = u'youtube'
            link["external"] = True
            link["embed"] = u'http://www.youtube.com/embed/%s?rel=0' % bibentry.fields[key]
            links.append(link)
