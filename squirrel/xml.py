import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

from .vars import logger, console
from .vars import PROJECT_FILENAME, WATCH_FILENAME
from .vars import project_file_path, watch_file_path


def build_project(data: dict, path):
    files = [
        os.path.join(path, PROJECT_FILENAME),
        os.path.join(path, WATCH_FILENAME)
    ]
    os.mkdir(path)

    for file in files:
        with open(file, 'w') as _:
            pass

    build_project_file(data, files[0])
    build_watch_file(files[1])


def build_project_file(data: dict, file):
    squirrel = ET.Element('squirrel', name=f"{data.get('name', '')}")

    _ = ET.SubElement(squirrel, 'path', src=f'{os.path.dirname(file)}')

    description = ET.SubElement(squirrel, 'description')
    description.text = data['description']

    due_date = ET.SubElement(squirrel, 'due-date')
    arg_due = data['due']
    due_date.text = arg_due.strftime('%d/%m/%Y') if arg_due is not None else None

    goal = ET.SubElement(squirrel, 'goal')
    goal.text = str(data['goal'])

    project_type = ET.SubElement(squirrel, 'project-type')
    p_type = data.get('project_type', 'text')
    project_type.text = p_type if p_type is not None else 'text'

    tree = ET.ElementTree(squirrel)
    ET.indent(tree)
    tree.write(file, encoding='utf-8', xml_declaration=True)


def build_watch_file(file):
    squirrel = ET.Element('squirrel')
    comment = ET.Comment(
        'This is a file generated by squirrel. Modify it at your own risk.')
    squirrel.insert(1, comment)
    tree = ET.ElementTree(squirrel)
    ET.indent(tree)
    tree.write(file, encoding='utf-8', xml_declaration=True)


def update_project_file(data: dict):
    path = project_file_path
    tree = parse(path)
    squirrel = tree.getroot()

    if (name := data.get('name')) is not None:
        squirrel.set('name', name)

    if (desc := data.get('description')) is not None:
        try:
            squirrel.find('description').text = desc
        except AttributeError:
            logger.error('[bold red blink]description[/] element was not found in the xml file'
                         ' try initializing the project again', extra={'markup': True})

    if (goal := data.get('goal')) is not None:
        try:
            squirrel.find('goal').text = str(goal)
        except AttributeError:
            logger.error('goal element was not found in the xml file'
                         ' try initializing the project again')

    if (due := data.get('due')) is not None:
        try:
            squirrel.find('due-date').text = due.strftime('%d/%m/%Y')
        except AttributeError:
            logger.error('due-date element was not found in the xml file'
                         'try init project again')

    if (project_type := data.get('project_type')) is not None:
        try:
            squirrel.find('project-type').text = project_type
        except AttributeError:
            logger.error('[bold red blink]project-type[/] element was not found in the xml file'
                         ' try initializing the project again', extra={'markup': True})

    tree.write(path, encoding='utf-8', xml_declaration=True)


def get_data_from_project_file(basedir=''):
    path = os.path.join(basedir, project_file_path)
    tree = parse(path)
    squirrel = tree.getroot()

    try:
        name = squirrel.attrib['name']
    except (AttributeError, KeyError):
        logger.error('Could not find name attribute')
        name = None

    try:
        path = squirrel.find('path').attrib['src']
    except (AttributeError, KeyError):
        logger.error('Could not find path field')
        path = None

    try:
        description = squirrel.find('description').text
    except (AttributeError, KeyError):
        logger.error('Could not find description field')
        description = None

    try:
        goal = squirrel.find('goal').text
    except (AttributeError, KeyError):
        logger.error('Could not find goal field')
        goal = None

    try:
        due_date = squirrel.find('due-date').text
    except (AttributeError, KeyError):
        logger.error('Could not find due_date field')
        due_date = None

    try:
        project_type = squirrel.find('project-type').text
    except (AttributeError, KeyError):
        logger.error('Could not find project-type field')
        project_type = None

    data = {
        'name': name,
        'path': path,
        'description': description,
        'goal': goal,
        'due-date': due_date,
        'project-type': project_type
    }
    return data


def get_watches_data():
    """returns all watches tag data with -1
    being the key of the last watches"""
    path = watch_file_path
    tree = parse(path)
    squirrel = tree.getroot()

    data = []
    try:
        for watches in squirrel.findall('watches'):
            date = watches.attrib['date']
            data.append((date,
                         watches.attrib['prev_count'],
                         get_watches_last_count(watches)))
    except (AttributeError, KeyError):
        sys.exit(1)

    return data


def get_watches_last_count(watches):
    if len(watches) == 0:
        return 0
    else:
        try:
            return watches[-1].text
        except AttributeError:
            return 0


def get_watches_entry(date):
    """returns the watches tag of the passed date and root element;
    defaults to (None, root)"""
    path = watch_file_path
    tree = parse(path)
    squirrel = tree.getroot()

    for watches in squirrel.findall('watches'):
        try:
            if watches.attrib['date'] == date.strftime('%d/%m/%Y'):
                return watches, squirrel
        except AttributeError:
            pass
        except KeyError:
            pass
    return None, squirrel


def make_watch_entry(parent, dt: datetime, value: int):
    watch = ET.SubElement(parent, 'watch', datetime=str(dt))
    watch.text = value
    return watch


def add_watch_entry(total, dt: datetime):
    """Add a watch tag to the watches tag of that date"""
    path = watch_file_path

    # We try to get the watch of the datetime passed
    watches_date, root = get_watches_entry(dt.date())

    if watches_date is not None:
        # If there are already <watch> inside <watches>, we have to verify that
        # they are different counts otherwise it's useless to record it
        # if in the other hand, we don't find any <watch> in <watches>
        # we should simply add a new <watch> tag
        if len(watches_date) > 0:
            if watches_date[-1].text != str(total):
                make_watch_entry(watches_date, str(dt), str(total))
            else:
                return False
        else:
            make_watch_entry(watches_date, str(dt), str(total))

    elif root is not None:
        # If haven't found <watches> tag, we need to create
        # a new one with a <watch> tag inside of it.
        try:
            prev_count = root[-1][-1].text
        except (IndexError, AttributeError):
            prev_count = str(0)

        watches = ET.SubElement(root,
                                'watches',
                                prev_count=prev_count,
                                date=dt.date().strftime('%d/%m/%Y'))
        make_watch_entry(watches_date, str(dt), str(total))
    else:
        return False

    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write(path, encoding='utf-8', xml_declaration=True)
    return True


def parse(path):
    try:
        parser_save_comments = ET.XMLParser(
            target=ET.TreeBuilder(insert_comments=True))
        tree = ET.parse(path, parser_save_comments)
        return tree
    except FileNotFoundError:
        console.print(f'Could not find {path!r};'\
                      ' Verify that project that initialized correctly.')
        sys.exit(1)
