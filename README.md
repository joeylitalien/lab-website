# Lab Website
This is the lab website for the graphics group at McGill University.

## Building website

This website is built by using [Jinja2](http://jinja.pocoo.org/docs/2.9/) templating language. To update the website, simply modify the necessary information in the `config/*.json` files and re-run `python build-website.py`. Templates used to generate the webpages can be found in `config/templates/`.

## Adding publications

To add a publication, add a BiBTeX entry with keyword `paperkey` in `pub-gen/templates/publications.bib`. Add any related files (such as video and slides) in `publications/`. Each file related to `paperkey` should be named `paperkey-filetype`. For thumbnail and teaser images, the files need to be in `publications/images/`. Keywords supported can be found in `pub-gen/templates/config.json`. To add Keynote presentation slides for instance, rename the slides file as `paperkey-slides.key` and add it to the `publications/` folder. For more info, consult `pub-gen/README.md`.

To generate all publications, run `python ../build-publications.py -p -i` within `pub-gen/templates`. This is based on Wojciech Jarosz's [open-source Python script](https://bitbucket.org/wkjarosz/academic-website-tools).
