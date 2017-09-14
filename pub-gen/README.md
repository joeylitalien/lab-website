# Academic website with publications

This contains my personal automation scripts to statically build my academic website from a BibTeX file and Jinja2 templates. Builds individual static pages, as well as a publication index, and individual publication project pages from a single BibTeX file.

## Example

The example directory includes a (simple) full working example. To generate the example website, run:

    cd example
    ../build-website -p -i -s
    open index.html

This should produce and `index.html` file, and two project pages. Without any styling, this should give you:
![Publications index unstyled](example/publications-index-unstyled.png)
and
![Project page unstyled](example/project-page-unstyled.png)


With more elaborate CSS styling, this could instead look like:
![Publications index unstyled](example/publications-index-styled.png)
and
![Project page unstyled](example/project-page-styled.png)
Check out my [website](https://www.cs.dartmouth.edu/~wjarosz/) for a full working example.

## Features

- Supports citation count scraping from Google scholar
- Each publication can have a project page generated, and can include an arbitrary number of downloadable files of various types
- Supports thumbnails and teaser images per publication
- Support for DOI links and ACM Author-izer links
- Customizable layout and styling of individual pages using Jinja templates and CSS
- Automatically generates list of peer-review conflicts from recent publications

## Dependencies

The toolchain relies on:

- [Pybtex python library](https://pybtex.org) - to parse the bib file. to install: `sudo pip install pybtex`
- [Unidecode](https://pypi.python.org/pypi/Unidecode) - to create ascii query for scholar search. to install: `sudo pip instasll unidecode`
- [Pillow](https://python-pillow.org) - to read images and get their width/height. to install: `sudo pip install Pillow`
- [Jinja2 templating system](http://jinja.pocoo.org) - to control the structure of the generated page using the data read from the bib file. to install: `sudo pip install Jinja2`
- [scholar.py](https://github.com/ckreibich/scholar.py) - query Google scholar

`scholar.py` is included in this repo, but you will need to install the other libraries on your system yourself.

## Overview and Usage

The basic idea behind the build-website.py script is to create an index of publications and individual project page for every entry in the bib file. This script needs to be re-run every time the bib file or Jinja templates are modified.

The script does not generate the html file directly, but instead loads a Jinja2 template, and passes in the data from the bib file into this template. This allows you to control how you'd like to structure/format your generated pages using the data available in your bib file.

### Standard bib field extraction and automatic file detection

The script parses the standard bibtex fields like title, authors, journal, abstract, etc. and makes these available as correspondingly named variables to the Jinja2 template.

The bib cite key is used as the base filename for both the generated `HTML` files and the data files the script tries to automatically associate with each publication (e.g. the PDF, supplemental zip files, videos, etc.). For instance, if there is a citekey `jarosz08beam`, the script will create `jarosz08beam.html`, and look for `jarosz08beam.pdf`, `jarosz08beam-slides.pdf`, `jarosz08beam.mp4`, and many other variations automatically.

The script currently recognizes a number of different categories of files. The basic categories are: "Paper", "Slide", and "Video" downloads. These categories collect all files within in the `pub-data-directory` directory (see below) which match the following patterns:

    Paper_downloads: cite_key + '(|-small|-supplemental|-supplemental-small|-tech|-errata)([1-9]|[1][0-9]|20)\.pdf'
    Slide_downloads: cite_key + '(-slides|-fast-forward)(|[1-9]|[1][0-9]|20)\.(pdf|key|ppt|pptx|zip|odp)'
    Video_downloads: cite_key + '(|-high|-web|-low|-iphone|-ipad)\.(mov|mp4|m4v|webm|mpg|avi)'

These regular expressions can be customized in the `config.json` file.

Any files automatically found in these categories are exposed to the Jinja2 template using lists named "*_downloads", where * is one of these category names. The individual entries in these lists contain attributes: `url`, `text_short`, `text_long`, and `type`, which you can use to populate your HTML through Jinja. For instance, you could create styled lists of all paper downloads like this in your Jinja2 template:

    {% for download in Paper_downloads %}
    <li class="{{download.type}}"><a href="{{download.url}}">{{download.text_long}}</a></li>
    {% endfor %}

You can configure the strings that are generated for `text_short` and `text_long` using "*-suffix-descriptions" in the `config.json` file.

Additionally, the script looks for a teaser and thumbnail image for each publication within `pub-data-directory/images/`, and exposes the following Jinja2 template variables:

    teaser_image: cite_key + '(-teaser)\.(.png|.jpeg|.jpg|.gif)'
    thumbnail_image: cite_key + '(-thumb)\.(.png|.jpeg|.jpg|.gif)'
    teaser_width: extracted from either the width of the teaser_image file, or using the manual override with the extra-caption-width field

### Extra BibTeX fields

To provide the template engine with additional information which cannot be found automatically and is not one of the standard bib fields, the script will look for addition "extra-" fields. For instance, `extra-caption`, if present, is used as the caption for the an optional teaser figure for the bib entry's publication page. These extra fields include:

- `extra-caption`: teaser caption
- `extra-caption-width`: explicit override for the width of the caption
- `extra-affiliation-n`: defines the name for the `n`-th affiliation on the paper
- `extra-author-affiliation-n`: this should be an integer, which specifies the index of the `n`-th authors affiliation
- `extra-acm-author-izer`: id for ACM author-izer, to provide a link to a free publisher version of the publication
- `extra-copyright`: a copyright notice for the publication

Sometimes, it may be necessary to add additional files which do not match these file naming convensions. For this, the script also looks for these extra bib fields:

- `extra-paper-download-n`: allows adding additional Paper downloads.
- `extra-slide-download-n`: allows adding additional Slide downloads.
- `extra-data-download-n`: allows adding additional data downloads.
- `extra-code-download-n`: allows adding auxiliary code downloads.
- `extra-youtube-download-n`: allows adding youtube videos. Type: youtube video id.

In all of the above, n=1..20. The youtube field above expects a youtube video id. All other fields expect an html description linked to the additional download.

### An example bib entry

A typical bib entry might look something like this:

    @article{novak14residual,
        author      = {Jan Novák and Andrew Selle and Wojciech Jarosz},
        title       = {Residual Ratio Tracking for Estimating Attenuation in Participating Media},
        journal     = {ACM Transactions on Graphics (Proceedings of SIGGRAPH Asia)},
        volume      = {33},
        number      = {6},
        year        = {2014},
        month       = nov,
        keywords    = {transmittance, fractional visibility, opacity, ray marching, woodcock tracking, delta tracking, pseudo-scattering, null-collision},
        abstract    = {Evaluating transmittance within participating media is a fundamental operation required by many light transport algorithms. We present <i>ratio tracking</i> and <i>residual tracking</i>, two complementary techniques that can be combined into an efficient, unbiased estimator for evaluating transmittance in complex heterogeneous media. In comparison to current approaches, our new estimator is unbiased, yields high efficiency, gracefully handles media with wavelength dependent extinction, and bridges the gap between closed form solutions and purely numerical, unbiased approaches. A key feature of ratio tracking is its ability to handle negative densities. This in turn enables us to separate the main part of the transmittance function, handle it analytically, and numerically estimate only the residual transmittance. In addition to proving the unbiasedness of our estimators, we perform an extensive empirical analysis to reveal parameters that lead to high efficiency. Finally, we describe how to integrate the new techniques into a production path tracer and demonstrate their benefits over traditional unbiased estimators.},
        doi         = {10.1145/2661229.2661292},
        extra-affiliation-1 = {Walt Disney Animation Studios},
        extra-affiliation-2 = {Disney Research Zürich},
        extra-author-affiliation-1 = {1,2},
        extra-author-affiliation-2 = {1},
        extra-author-affiliation-3 = {2},
        extra-caption = {A cloudy sky rendered with our residual ratio tracking estimator for computing transmittance in heterogeneous volumes. Our technique is unbiased, outperforms the delta tracking-based estimator (<b>b</b>), and fits well into path-tracing, production frameworks. The insets show renderings of absorptive-only (top) and scattering (bottom) clouds; the transmittance was estimated using delta tracking (<b>b</b>), ratio tracking (<b>c</b>), and residual ratio tracking (<b>d</b>) with a roughly equal cost reported as the number of extinction coefficient evaluations.},
        extra-acm-author-izer = {N19093},
        extra-copyright = ACM_COPY
    }

## JSON configuration file

The script uses a `config.json` file to configure various settings of the build process:

- `bib-file`: path and filename of the bib file
- `author-database`: the author database matching author names to website addresses
- `pub-data-directory`: where to search for data files associated with each publication
- `jnj-templates-root`: root directory where for Jinja templates
- `pub-index-template`: path and base filename (relative to `jnj-templates-root` and without the `.jnj` extension) of the Jinja2 template for the publications index
- `pub-pages-template`: path and base filename (relative to `jnj-templates-root` and without the `.jnj` extension) of the Jinja2 template for a publication project page
- `static-page-templates`: a list of static Jinja2 template files (relative to `jnj-templates-root` and without the `.jnj` extension) to generate
- `static-page-output-root`: output directory for the static pages
- `pub-index-output-directory`: output directory for the `.html` publication index
- `pub-pages-output-directory`: output directory for the publication project pages

Additionally, many of the regular expressions and text strings that the build script uses to automatically detect and describe a files can be customized in the config file. These entries *must* be defined for the build script to work. See the `example` subdirectory for an example, and use this as a starting point for your `config.json` file


## Issues and TODOs

- Scraping citation counts accesses Google scholar too often and too quickly, and can lead to google temporarily blocking your IP address.
- Need to add more complete documentation


## Contributing

I am not a Python programmer, so much of this code may not be the most elegant of even correct way of doing things, but it got the job done for me. If you want to help improve these tools, let me know. I am most interested in bug-fixes and improvements to make the whole system more elegant or general while maintaining the current functionality. Since I am mostly satisfied with the available functionality, I will consider push-requests with additional features only if they do not significantly increase the complexity of the code.

## License

Since this is mostly of interest to the academic community, and I'd like improvements to be contributed back to the community, I'm licensing these scripts under the GPLv3.
