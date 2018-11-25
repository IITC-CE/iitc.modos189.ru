"""
Usage:
  main.py --template=<path> --static=<path> --config=FILE --page=<pg>

Options:
  -h --help
"""
from docopt import docopt
from jinja2 import Environment, FileSystemLoader
import urllib.request
import json
import os


def save_config():
    with open(arguments['--config'], 'w') as _f:
        json.dump(config, _f)


def parse_user_script(path):
    data = {}
    with open(path) as file:
        for line in file:
            if "==UserScript==" in line:
                continue
            if "==/UserScript==" in line:
                return data

            line = line.strip()
            sp = line.split()
            data[sp[1]] = ' '.join(sp[2:])


def parse_build(release_type):
    data = {
        release_type + '_plugins': {
            "Portal Info": {'name': "Portal Info",
                            'desc': "Enhanced information on the selected portal",
                            'plugins': []},
            "Info": {'name': "Info",
                     'desc': "Display additional information",
                     'plugins': []},
            "Keys": {'name': "Keys",
                     'desc': "Manual key management",
                     'plugins': []},
            "Controls": {'name': "Controls",
                         'desc': "Map controls/widgets",
                         'plugins': []},
            "Highlighter": {'name': "Highlighter",
                            'desc': "Portal highlighters",
                            'plugins': []},
            "Layer": {'name': "Layer",
                      'desc': "Additional map layers",
                      'plugins': []},
            "Map Tiles": {'name': "Map Tiles",
                          'desc': "Alternative map layers",
                          'plugins': []},
            "Tweaks": {'name': "Tweaks",
                       'desc': "Adjust IITC settings",
                       'plugins': []},
            "Misc": {'name': "Misc",
                     'desc': "Unclassified plugins",
                     'plugins': []},
            "Obsolete": {'name': "Obsolete",
                         'desc': "Plugins that are no longer recommended, due to being superceded by others or similar",
                         'plugins': []},
            "Deleted": {'name': "Deleted",
                        'desc': "Deleted plugins - listed here for reference only. No download available",
                        'plugins': []},
        }}

    folder = arguments['--static'] + "/build/" + release_type + "/"
    info = parse_user_script(folder + "total-conversion-build.user.js")
    data['release_iitc_version'] = info['@version']

    plugins = os.listdir(folder + "plugins")
    plugins = filter(lambda x: x.endswith('.user.js'), plugins)
    for filename in plugins:
        info = parse_user_script(folder + "plugins/" + filename)
        category = info.get('@category')
        if not category or category not in data[release_type + '_plugins']:
            category = "Misc"
        data[release_type + '_plugins'][category]['plugins'].append({
            'name': info['@name'],
            'id': info['@id'],
            'version': info['@version'],
            'filename': filename,
            'desc': info['@description'],
        })
    return data


def get_telegram_widget(channel, _id):
    url = 'https://t.me/%s/%i?embed=1' % (channel, _id)
    response = urllib.request.urlopen(url, timeout=10)
    data = response.read()
    html = data.decode('utf-8')

    if "tgme_widget_message_author" in html:
        html = html[html.find('<div class="tgme_widget_message"'):]
        html = html[:html.find('<script')]
        return html


def generate_page(page):
    template = env.get_template(page)

    markers = config.copy()
    markers['active_page'] = page
    if page == 'index.html':
        _id = config['telegram_channel_last_id']
        widget = get_telegram_widget(config['telegram_channel_name'], _id + 1)
        if widget is None:
            widget = get_telegram_widget(config['telegram_channel_name'], _id)
        else:
            config['telegram_channel_last_id'] += 1
            save_config()
        if widget is None:
            print("Error updating telegram")
            return
        markers['telegram_widget'] = widget

    if page == 'download_desktop.html':
        data = parse_build('release')
        markers.update(data)

    html = template.render(markers)
    path = arguments['--static'] + "/" + page
    with open(path, "w") as fh:
        fh.write(html)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    with open(arguments['--config'], 'r') as f:
        config = json.load(f)

    env = Environment(
        loader=FileSystemLoader(arguments['--template']),
        trim_blocks=True
    )

    if arguments['--page'] == "all":
        files = os.listdir(arguments['--template'])
        files = filter(lambda x: x.endswith('.html'), files)
    else:
        files = [arguments['--page'] + '.html']

    for _page in files:
        if _page == "__base__.html":
            continue
        generate_page(_page)
