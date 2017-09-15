#!/usr/bin/python
# coding: utf-8

import jinja2
import json
import os
import datetime

PATH = os.path.dirname(os.path.abspath(__file__))

def create_pages(env):
    with open('people.json') as fp:    
        people = json.load(fp)
    with open('news.json') as fp:
        news = json.load(fp)
        news.sort(key=lambda x: datetime.datetime.strptime(x['date'], '%Y.%m.%d'))
    with open('featured.json') as fp:
        featured = json.load(fp)
    with open('research.json') as fp:
        research = json.load(fp)
    with open('courses.json') as fp:
        courses = json.load(fp)

    # Render home page
    template = env.get_template('templates/home.html')
    template.stream(people=people, 
                    news=news,
                    research=research,
                    courses=courses,
                    featured=featured).dump('../index.html')

    # Render news page
    template = env.get_template('templates/news.html')
    template.stream(news=news).dump('../news.html')

if __name__ == '__main__':
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(PATH),
                             trim_blocks=True)

    create_pages(env)
    
