#! /usr/bin/env python3

import datetime
from argparse import ArgumentParser
from base64 import b64decode
from os import path, walk, remove, getcwd
from re import findall
from typing import Callable
from zipfile import ZipFile, ZIP_DEFLATED

import requests
import requests.exceptions
import selenium.common.exceptions
from selenium.webdriver import Firefox, FirefoxOptions, FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from src.form_text import color_text
from src.logo import name
from src.manager import Manager, Xpaths

module_name = 'FisherMan: Extract information from facebook profiles.'
__version__ = "3.2.1"


class Fisher:
    def __init__(self):
        parser = ArgumentParser(description=f'{module_name} (Version {__version__})')
        exclusive_group = parser.add_mutually_exclusive_group()

        parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}',
                            help='Shows the current version of the program.')

        exclusive_group.add_argument('-u', '--username', action='store', nargs='+', required=False,
                                     type=str, help='Defines one or more users for the search.')

        exclusive_group.add_argument("-i", "--id", action="store", nargs="+", required=False, type=str,
                                     help="Set the profile identification number.")

        exclusive_group.add_argument('--use-txt', action='store', required=False, dest='txt', metavar='TXT_FILE',
                                     type=str, nargs=1,
                                     help='Replaces the USERNAME parameter with a user list in a txt.')

        parser.add_argument('-sf', '--scrape-family', action='store_true', required=False, dest='scrpfm',
                            help='If this parameter is passed, '
                                 'the information from family members will be scraped if available.')

        parser.add_argument("--specify", action="store", nargs="+", required=False, type=int,
                            choices=[0, 1, 2, 3, 4, 5],
                            help="Use the index number to return a specific part of the page. "
                                 "about: 0, about_contact_and_basic_info: 1, "
                                 "about_family_and_relationships: 2, "
                                 "about_details: 3, "
                                 "about_work_and_education: 4, "
                                 "about_places: 5.")

        parser.add_argument("-s", "--several", action="store_true", required=False,
                            help="Returns extra data like profile picture, number of followers and friends.")

        parser.add_argument('-b', '--browser', action='store_true', required=False,
                            help='Opens the browser/bot.')

        parser.add_argument('--email', action='store', metavar='EMAIL',
                            required=False, type=str, nargs=1,
                            help='If the profile is blocked, you can define your account, '
                                 'however you have the search user in your friends list.')

        parser.add_argument('--password', action='store', metavar='PASSWORD', dest='pwd', required=False, type=str,
                            nargs=1,
                            help='Set the password for your facebook account, '
                                 'this parameter has to be used with --email.')

        parser.add_argument('-o', '--file-output', action='store_true', required=False, dest='out',
                            help='Save the output data to a .txt file.')

        parser.add_argument("-c", "--compact", action="store_true", required=False,
                            help="Compress all .txt files. Use together with -o.")

        parser.add_argument('-v', '-d', '--verbose', '--debug', action='store_true', required=False,
                            help='It shows in detail the data search process.')

        print(color_text('cyan', name))
        self.args = parser.parse_args()


def update():
    try:
        r = requests.get("https://raw.githubusercontent.com/Godofcoffe/FisherMan/main/fisherman.py")

        remote_version = str(findall('__version__ = "(.*)"', r.text)[0])
        local_version = __version__

        if remote_version != local_version:
            print(color_text('yellow', "Update Available!\n" +
                             f"You are running version {local_version}. Version {remote_version} "
                             f"is available at https://github.com/Godofcoffe/FisherMan"))
    except Exception as error:
        print(color_text('red', f"A problem occured while checking for an update: {error}"))


def upload_txt_file(name_file: str):
    """
        Load a file to replace the username parameter.

        :param name_file: txt file name.

        :return: A list with each line of the file.
    """
    if path.isfile(name_file):
        try:
            with open(name_file, 'r') as txt:
                users_txt = txt.readlines()
        except Exception as error:
            print(color_text('red', f'An error has occurred: {error}'))
        else:
            return users_txt
    else:
        raise Exception(color_text("red", "INVALID FILE!"))


def compact():
    """
        Compress all .txt with the exception of requirements.txt.
    """
    with ZipFile(f"{str(datetime.datetime.now())[:16]}", "w", ZIP_DEFLATED) as zip_output:
        for root, dirs, files in walk(getcwd()):
            for archive in files:
                _file_name, extension = path.splitext(archive)
                if (extension.lower() == ".txt" and _file_name != "requeriments") or extension.lower() == ".jpeg":
                    zip_output.write(archive)
                    remove(archive)
    print(f'[{color_text("green", "+")}] successful compression')


def check_connection():
    """
        Check the internet connection.
    """
    try:
        requests.get("https://google.com")
    except requests.exceptions.ConnectionError:
        raise Exception("There is no internet connection.")


def extra_data(parse, brw: Firefox, user: str):
    """
        Save other data outside the about user page.

        :param parse: ArgParse instance namespace arguments to change code flow.
        :param brw: Instance of WebDriver.
        :param user: username to search.
    """
    if parse.id:
        brw.get(f"{manager.get_id_prefix() + user}")
    else:
        brw.get(f"{manager.get_url() + user}")

    followers = None
    friends = None

    wbw = WebDriverWait(brw, 10)
    xpaths = Xpaths()

    def collection_by_xpath(expected: Callable, xpath: str):
        try:
            wbw.until(expected((By.XPATH, xpath)))
        except selenium.common.exceptions.NoSuchElementException:
            print(f'[{color_text("red", "-")}] non-existent element')
        except selenium.common.exceptions.TimeoutException:
            if parse.verbose:
                print(f'[{color_text("yellow", "-")}] timed out to get the extra data')
            else:
                print(f'[{color_text("yellow", "-")}] time limit exceeded')
        else:
            return brw.find_element_by_xpath(xpath)

    img = collection_by_xpath(ec.element_to_be_clickable, xpaths.picture)
    img.screenshot(f"{user}_profile_picture.png")
    print(f'[{color_text("green", "+")}] picture saved')

    element = collection_by_xpath(ec.visibility_of_element_located, xpaths.bio).text
    if element:
        bio = element
    else:
        bio = None

    followers = str(collection_by_xpath(ec.visibility_of_element_located, xpaths.followers).text).split()[0]

    try:
        element = collection_by_xpath(ec.visibility_of_element_located, xpaths.friends)
        element = element.find_elements_by_tag_name("span")[2].text
    except IndexError:
        print(f'[{color_text("red", "-")}] There is no number of friends to catch')
    else:
        friends = element

    if parse.txt:
        _file_name = rf"extraData-{user}-{str(datetime.datetime.now())[:16]}.txt"
        if parse.compact:
            _file_name = f"extraData-{user}.txt"
        with open(_file_name, "w+") as extra:
            extra.write(f"Bio: {bio}")
            extra.write(f"Followers: {followers}")
            extra.write(f"Friends: {friends}")
    else:
        # in the future to add more data variables, put in the dict
        manager.add_extras(user, {"Bio": bio, "Followers": followers, "Friends": friends})


def scrape(parse, brw: Firefox, items: list[str]):
    """
        Extract certain information from the html of an item in the list provided.

        :param parse: ArgParse instance namespace arguments to change code flow.
        :param brw: Instance of WebDriver.
        :param items: List of users to apply to scrape.

        All data is stored in a list for each iterable items.
    """

    branch = ['/about', '/about_contact_and_basic_info', '/about_family_and_relationships', '/about_details',
              '/about_work_and_education', '/about_places']
    branch_id = [bn.replace("/", "&sk=") for bn in branch]
    wbw = WebDriverWait(brw, 10)

    def thin_out(user: str):
        """
            Username Refiner.

            :param user: user to be refined.

            This function returns a username that is acceptable for the script to run correctly.
        """

        if user.isnumeric():
            if "facebook.com" in user:
                user = user[user.index("=") + 1:]
            return manager.get_id_prefix(), user
        else:
            if "facebook.com" in user:
                user = user[user.index("/", 9) + 1:]
            return manager.get_url(), user

    for usrs in items:
        prefix, usrs = thin_out(usrs)
        temp_data = []
        print(f'[{color_text("white", "*")}] Coming in {prefix + usrs}')

        # here modifies the branch list to iterate only the parameter items --specify
        if parse.specify:
            temp_branch = []
            for index in parse.specify:
                temp_branch.append(branch[index])
                if parse.verbose:
                    print(f'[{color_text("green", "+")}] branch {index} added to url')
            branch = temp_branch

        # search for extra data
        if parse.several:
            if parse.verbose:
                print(f'[{color_text("blue", "+")}] getting extra data...')
            extra_data(parse, brw, usrs)

        for bn in branch if not usrs.isnumeric() else branch_id:
            brw.get(f'{prefix + usrs + bn}')
            try:
                output = wbw.until(ec.presence_of_element_located((By.CLASS_NAME, 'f7vcsfb0')))

            except selenium.common.exceptions.TimeoutException:
                print(f'[{color_text("yellow", "-")}] time limit exceeded')

            except Exception as error:
                print(f'[{color_text("red", "-")}] class f7vcsfb0 did not return')
                if parse.verbose:
                    print(color_text("yellow", f"error details:\n{error}"))
            else:
                if parse.verbose:
                    print(f'[{color_text("blue", "+")}] Collecting data from: div.f7vcsfb0')
                else:
                    print(f'[{color_text("blue", "+")}] collecting data ...')
                temp_data.append(output.text)

                # check to start scrape family members
                if "about_family_and_relationships" in bn:
                    members = output.find_elements(By.TAG_NAME, "a")
                    if members and parse.scrpfm:
                        members_list = []
                        for link in members:
                            members_list.append(link.get_attribute('href'))
                        manager.add_affluent(usrs, members_list)

        # this scope will only be executed if the list of "affluents" is not empty.
        if manager.get_affluent():
            div = "\n\n\n" + '=' * 60 + "\n\n\n"

            for memb in manager.get_affluent()[usrs]:
                print()
                print(f'[{color_text("white", "*")}] Coming in {memb}')
                temp_data.append(div)

                # search for extra data
                if parse.several:
                    if parse.verbose:
                        print(f'[{color_text("blue", "+")}] getting extra data...')
                    extra_data(parse, brw, memb)

                for bn in branch if not memb.isnumeric() else branch_id:
                    brw.get(f'{memb + bn}')
                    try:
                        output2 = wbw.until(ec.presence_of_element_located((By.CLASS_NAME,
                                                                            'f7vcsfb0')))

                    except selenium.common.exceptions.TimeoutException:
                        print(f'[{color_text("yellow", "-")}] time limit exceeded')

                    except Exception as error:
                        print(f'[{color_text("red", "-")}] class f7vcsfb0 did not return')
                        if parse.verbose:
                            print(color_text("yellow", f"error details:\n{error}"))
                    else:
                        if parse.verbose:
                            print(f'[{color_text("blue", "+")}] Collecting data from: div.f7vcsfb0')
                        else:
                            print(f'[{color_text("blue", "+")}] collecting data ...')
                        temp_data.append(output2.text)

        # complete addition of all data
        manager.add_data(usrs, temp_data)


def login(parse, brw: Firefox):
    """
        Execute the login on the page.

        :param parse: ArgParse instance namespace arguments to change code flow.
        :param brw: Instance of WebDriver.
    """
    brw.get(manager.get_url())
    wbw = WebDriverWait(brw, 10)

    email = wbw.until(ec.element_to_be_clickable((By.NAME, "email")))
    pwd = wbw.until(ec.element_to_be_clickable((By.NAME, "pass")))
    ok = wbw.until(ec.element_to_be_clickable((By.NAME, "login")))

    email.clear()
    pwd.clear()

    # custom accounts will only be applied if both fields are not empty
    if parse.email is None or parse.args.pwd is None:
        if parse.verbose:
            print(f'[{color_text("white", "*")}] adding fake email: {manager.get_email()}')
            email.send_keys(manager.get_email())
            print(f'[{color_text("white", "*")}] adding password: ...')
            pwd.send_keys(b64decode(manager.get_pass()).decode("utf-8"))
        else:
            print(f'[{color_text("white", "*")}] logging into the account: {manager.get_email()}')
            email.send_keys(manager.get_email())
            pwd.send_keys(b64decode(manager.get_pass()).decode("utf-8"))
    else:
        if parse.verbose:
            print(f'adding email: {parse.email}')
            email.send_keys(parse.args.email)
            print('adding password: ...')
            pwd.send_keys(parse.pwd)
        else:
            print(f'logging into the account: {parse.email}')
            email.send_keys(parse.email)
            pwd.send_keys(parse.pwd)
    ok.click()
    if parse.verbose:
        print(f'[{color_text("green", "+")}] successfully logged in')


def init(parse):
    """
        Start the webdriver.

        :param parse: ArgParse instance namespace arguments to change code flow.
    """

    # browser settings
    _profile = FirefoxProfile()
    _options = FirefoxOptions()

    # eliminate pop-ups
    _profile.set_preference("dom.popup_maximum", 0)
    _profile.set_preference("privacy.popups.showBrowserMessage", False)

    # incognito
    _profile.set_preference("browser.privatebrowsing.autostart", True)
    _options.add_argument("--incognito")

    # arguments
    _options.add_argument('--disable-blink-features=AutomationControlled')
    _options.add_argument("--disable-extensions")
    # _options.add_argument('--profile-directory=Default')
    _options.add_argument("--disable-plugins-discovery")

    configs = {"firefox_profile": _profile, "options": _options}
    if not parse.browser:
        if parse.verbose:
            print(f'[{color_text("blue", "*")}] Starting in hidden mode')
        configs["options"].add_argument("--headless")
        configs["options"].add_argument("--start-maximized")

    if parse.verbose:
        print(f'[{color_text("white", "*")}] Opening browser ...')
    try:
        engine = Firefox(**configs)
    except Exception as error:
        print(color_text("red",
                         f'The executable "geckodriver" was not found or the browser "Firefox" is not installed.'))
        print(color_text("yellow", f"error details:\n{error}"))
    else:
        # others arguments
        engine.delete_all_cookies()
        return engine


def out_file(parse, _input: list[str]):
    """
        Create the .txt output of the -o parameter.

        :param parse: ArgParse instance namespace arguments to change code flow.
        :param _input: The list that will be iterated over each line of the file, in this case it is the list of users.
    """
    for usr in _input:
        file_name = rf"{usr}-{str(datetime.datetime.now())[:16]}.txt"
        if parse.args.compact:
            file_name = usr + ".txt"
        with open(file_name, 'w+') as file:
            for data_list in manager.get_data()[usr]:
                file.writelines(data_list)

    print(f'[{color_text("green", "+")}] .txt file(s) created')
    if parse.args.compact:
        if parse.args.verbose:
            print(f'[{color_text("white", "*")}] preparing compaction...')
        compact()


if __name__ == '__main__':
    check_connection()
    fs = Fisher()
    manager = Manager()
    ARGS = fs.args
    update()
    browser = init(ARGS)
    login(ARGS, browser)
    if ARGS.txt:
        scrape(ARGS, browser, upload_txt_file(ARGS.txt[0]))
    elif ARGS.username:
        scrape(ARGS, browser, ARGS.username)
    elif ARGS.id:
        scrape(ARGS, browser, ARGS.id)
    browser.quit()
    print()

    if ARGS.out:  # .txt output creation
        if ARGS.username:
            out_file(ARGS, ARGS.username)
        elif ARGS.txt:
            out_file(ARGS, ARGS.txt)
        elif ARGS.id:
            out_file(ARGS, ARGS.id)
    else:
        print(color_text('green', 'Information found:'))
        print('-' * 60)
        for profile in manager.get_all_keys()[2]:
            for data in manager.get_data()[profile]:
                print(data)
                print()
                print('-' * 60)

            if ARGS.several:
                print("EXTRAS:")
                for data_extra in manager.get_extras()[profile].items():
                    print(f"{data_extra[0]:10}: {data_extra[1]}")
