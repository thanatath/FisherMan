#! /usr/bin/env python3

import datetime
from argparse import ArgumentParser
from base64 import b64decode
from os import path, walk, remove, getcwd, system
from re import findall
from zipfile import ZipFile, ZIP_DEFLATED

from requests import get
from selenium.webdriver import Firefox, FirefoxOptions, FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from src.form_text import color_text
from src.logo import name

module_name = 'FisherMan: Extract information from facebook profiles.'
__version__ = "3.1.0"


class Fisher:
    def __init__(self):
        parser = ArgumentParser(description=f'{module_name} (Version {__version__})')

        parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}',
                            help='Shows the current version of the program.')

        parser.add_argument('-u', '--username', action='store', nargs='+', required=False, dest='usersnames',
                            type=str, help='Defines one or more users for the search.')

        parser.add_argument('-sf', '--scrape-family', action='store_true', required=False, dest='scrpfm',
                            help='If this parameter is passed, '
                                 'the information from family members will be scraped if available.')

        parser.add_argument("--specify", action="store", nargs="+", required=False, dest="index",
                            type=int, choices=[0, 1, 2, 3, 4, 5],
                            help="Use the index number to return a specific part of the page. "
                                 "about: 0, about_contact_and_basic_info: 1, "
                                 "about_family_and_relationships: 2, "
                                 "about_details: 3, "
                                 "about_work_and_education: 4, "
                                 "about_places: 5.")

        parser.add_argument("-s", "--several", action="store_true", required=False, dest="several",
                            help="Returns extra data like profile picture and number of followers.")

        parser.add_argument('-b', '--browser', action='store_true', dest='browser', required=False,
                            help='Opens the browser/bot.')

        parser.add_argument('--email', action='store', metavar='EMAIL', dest='email',
                            required=False, type=str,
                            help='If the profile is blocked, you can define your account, '
                                 'however you have the search user in your friends list.')

        parser.add_argument('--password', action='store', metavar='PASSWORD', dest='pwd', required=False, type=str,
                            help='Set the password for your facebook account, '
                                 'this parameter has to be used with --email.')

        parser.add_argument('--use-txt', action='store', required=False, dest='txt', metavar='TXT_FILE', type=str,
                            help='Replaces the USERSNAMES parameter with a user list in a txt.')

        parser.add_argument('-o', '--file-output', action='store_true', required=False, dest='out',
                            help='Save the output data to a .txt file.')

        parser.add_argument("-c", "--compact", action="store_true", required=False, dest="comp",
                            help="Compress all .txt files. Use together with -o.")

        parser.add_argument('-v', '-d', '--verbose', '--debug', action='store_true', required=False, dest='verb',
                            help='It shows in detail the data search process.')

        print(color_text('blue', name))
        self.args = parser.parse_args()


class Manager:
    def __init__(self):
        self.__url__ = 'https://facebook.com/'
        self.__fake_email__ = 'submarino.sub.aquatico@outlook.com'
        self.__password__ = 'MDBjbGVwdG9tYW5pYWNvMDA='
        self.__data__ = []
        self.__affluent__ = []
        self.__extras__ = []

    def clean_all(self):
        self.__data__.clear()
        self.__affluent__.clear()
        self.__extras__.clear()

    def clean_data(self):
        self.__data__.clear()

    def clean_affluent(self):
        self.__affluent__.clear()

    def clean_extras(self):
        self.__extras__.clear()

    def set_email(self, string: str):
        self.__fake_email__ = string

    def set_pass(self, string: str):
        self.__password__ = string

    def set_data(self, item_list: list):
        self.__data__ = item_list

    def set_affluent(self, item_list: list):
        self.__affluent__ = item_list

    def set_extras(self, item_list: list):
        self.__extras__ = item_list

    def add_data(self, string):
        self.__data__.append(string)

    def add_affluent(self, string):
        self.__affluent__.append(string)

    def add_extras(self, string):
        self.__extras__.append(string)

    def get_url(self):
        return self.__url__

    def get_email(self):
        return self.__fake_email__

    def get_pass(self):
        return self.__password__

    def get_data(self):
        return self.__data__

    def get_affluent(self):
        return self.__affluent__

    def get_extras(self):
        return self.__extras__


def update():
    try:
        r = get("https://raw.githubusercontent.com/Godofcoffe/FisherMan/main/fisherman.py")

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
        color_text("red", "INVALID FILE!")


def compact():
    """
        Compress all .txt with the exception of requirements.txt.
    """
    with ZipFile(f"{str(datetime.datetime.now())[:16]}", "w", ZIP_DEFLATED) as zip_output:
        for root, dirs, files in walk(getcwd()):
            for archive in files:
                _file_name, extension = path.splitext(archive)
                if (extension == ".txt" and _file_name != "requeriments") or extension == ".jpeg":
                    zip_output.write(archive)
                    remove(archive)
    print(f'[{color_text("green", "+")}] successful compression')


def exec_script(brw: Firefox, script: str):
    """
        Runs a javascript script in the browser.

        :param brw: Instance of WebDriver.
        :param script: Script to be run on console.
        :return: A data script.

        Example script parameter: "return document.getElementById("fish");"
    """
    return brw.execute_script(script)


manager = Manager()


def extra_data(args, brw: Firefox, user: str):
    img = exec_script(brw, "return document.getElementsByTagName('image')[0].getAttribute('xlink:href');")
    followes = exec_script(brw, "return document.getElementsByTagNae('a')[20].innerText;")
    system(rf"wget '{img}'")
    if args.txt:
        _file_name = rf"{user}-{str(datetime.datetime.now())[:16]}.txt"
        if args.comp:
            _file_name = f"extraData-{user}.txt"
        with open(_file_name, "w+") as extra:
            extra.write(followes)
    else:

        # in the future to add more data variables, put in the list
        manager.add_extras([followes])


def scrape(parse, brw: Firefox, items: list):
    """
        Extract certain information from the html of an item in the list provided.

        :param parse: ArgParse instance namespace arguments to change code flow.
        :param brw: Instance of WebDriver.
        :param items: List of users to apply to scrape.

        All data is stored in a list for each iterable items.
    """

    branch = ['/about', '/about_contact_and_basic_info', '/about_family_and_relationships', '/about_details',
              '/about_work_and_education', '/about_places']
    for usrs in items:
        temp_data = []
        print(f'[{color_text("white", "*")}] Coming in {manager.get_url() + usrs}')

        # here modifies the branch list to iterate only the parameter items --specify
        if parse.index:
            temp_branch = []
            for i in parse.index:
                temp_branch.append(branch[i])
                if parse.verb:
                    print(f'[{color_text("green", "+")}] branch {i} added to url')
            branch = temp_branch

        # search for extra data
        if parse.several:
            extra_data(parse, brw, usrs)

        for bn in branch:
            brw.get(f'{manager.get_url() + usrs + bn}')
            try:
                output = WebDriverWait(brw, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'f7vcsfb0')))
            except Exception as error:
                print(f'[{color_text("red", "-")}] class f7vcsfb0 did not return')
                print(color_text("yellow", f"error details:\n{error}"))
            else:
                if parse.verb:
                    print(f'[{color_text("blue", "+")}] Collecting data from: div.f7vcsfb0')
                else:
                    print(f'[{color_text("blue", "+")}] collecting data ...')
                temp_data.append(output.text)

                # check to start scrape family members
                if bn == '/about_family_and_relationships':
                    members = output.find_elements(By.TAG_NAME, "a")
                    if members and parse.scrpfm:
                        for link in members:
                            manager.add_affluent(link.get_attribute('href'))

        # this scope will only be executed if the list of "affluents" is not empty.
        if manager.get_affluent():
            div = "\n\n\n" + '=' * 70 + "\n\n\n"
            bar = "\n" + "*" * 70 + "\n"
            for memb in manager.get_affluent():
                print()
                print(f'[{color_text("white", "*")}] Coming in {memb}')
                temp_data.append(div)

                # search for extra data
                if parse.several:
                    extra_data(parse, brw, memb)

                for bn in branch:
                    brw.get(f'{memb + bn}')
                    try:
                        output2 = WebDriverWait(brw, 10).until(ec.presence_of_element_located((By.CLASS_NAME,
                                                                                               'f7vcsfb0')))
                    except Exception as error:
                        print(f'[{color_text("red", "-")}] class f7vcsfb0 did not return')
                        print(color_text("yellow", f"error details:\n{error}"))
                    else:
                        if parse.verb:
                            print(f'[{color_text("blue", "+")}] Collecting data from: div.f7vcsfb0')
                        else:
                            print(f'[{color_text("blue", "+")}] collecting data ...')
                        temp_data.append(output2.text + bar)

            # add a bar to separate between users
            temp_data.append(div)
        # complete addition of all data
        manager.add_data(temp_data)


def login(parse, brw: Firefox):
    """
        Execute the login on the page.

        :param parse: ArgParse instance namespace arguments to change code flow.
        :param brw: Instance of WebDriver.
    """
    brw.get(manager.get_url())

    email = WebDriverWait(brw, 10).until(ec.element_to_be_clickable((By.NAME, "email")))
    pwd = WebDriverWait(brw, 10).until(ec.element_to_be_clickable((By.NAME, "pass")))
    ok = WebDriverWait(brw, 10).until(ec.element_to_be_clickable((By.NAME, "login")))

    email.clear()
    pwd.clear()

    # custom accounts will only be applied if both fields are not empty
    if parse.email is None or parse.args.pwd is None:
        if parse.verb:
            print(f'[{color_text("white", "*")}] adding fake email: {manager.get_email()}')
            email.send_keys(manager.get_email())
            print(f'[{color_text("white", "*")}] adding password: ...')
            pwd.send_keys(b64decode(manager.get_pass()).decode("utf-8"))
        else:
            print(f'[{color_text("white", "*")}] logging into the account: {manager.get_email()}')
            email.send_keys(manager.get_email())
            pwd.send_keys(b64decode(manager.get_pass()).decode("utf-8"))
    else:
        if parse.verb:
            print(f'adding email: {parse.email}')
            email.send_keys(parse.args.email)
            print('adding password: ...')
            pwd.send_keys(parse.pwd)
        else:
            print(f'logging into the account: {parse.email}')
            email.send_keys(parse.email)
            pwd.send_keys(parse.pwd)
    ok.click()
    if parse.verb:
        print(f'[{color_text("green", "+")}] successfully logged in')


def main(args):
    """
        Main function.

        :param args: ArgParse instance namespace arguments to change code flow.

        Where the other functions and flow decisions are executed.
    """

    # browser settings
    profile = FirefoxProfile()
    options = FirefoxOptions()

    # eliminate pop-ups
    profile.set_preference("dom.popup_maximum", 0)
    profile.set_preference("privacy.popups.showBrowserMessage", False)

    # leaves the browser hidden
    options.add_argument("--headless")
    configs = {"firefox_profile": profile}
    if not args.browser:
        if args.verb:
            print(f'[{color_text("blue", "*")}] Starting in hidden mode')
        configs["options"] = options
    if args.verb:
        print(f'[{color_text("white", "*")}] Opening browser ...')

    try:
        browser = Firefox(**configs)
    except Exception as error:
        print(color_text("red",
                         f'The executable "geckodriver" was not found or the browser "Firefox" is not installed.'))
        print(color_text("yellow", f"error details:\n{error}"))
    else:
        login(args, browser)
        if args.usersnames is None:
            scrape(args, browser, upload_txt_file(args.txt))
        else:
            scrape(args, browser, args.usersnames)
        browser.quit()


if __name__ == '__main__':
    fs = Fisher()
    update()
    main(fs.args)
    txt_file = fs.args.txt
    print()

    if fs.args.out:  # .txt output creation
        if fs.args.usersnames is None:
            for usr in upload_txt_file(txt_file):
                file_name = rf"{usr}-{str(datetime.datetime.now())[:16]}.txt"
                if fs.args.comp:
                    file_name = usr + ".txt"
                with open(file_name, 'a+') as file:
                    for data_list in manager.get_data():
                        file.writelines(data_list)

        else:
            for usr2 in fs.args.usersnames:
                file_name = rf"{usr2}-{str(datetime.datetime.now())[:16]}.txt"
                if fs.args.comp:
                    file_name = usr2 + ".txt"
                with open(file_name, 'a+') as file:
                    for data_list in manager.get_data():
                        file.writelines(data_list)

        print(f'[{color_text("green", "+")}] .txt file(s) created')
        if fs.args.comp:
            if fs.args.verb:
                print(f'[{color_text("white", "*")}] preparing compaction...')
            compact()

    else:
        print(color_text('green', 'Information found:'))
        print('-' * 60)
        for data_list in manager.get_data():
            for data in data_list:
                print(data)
                print()
                print('-' * 50)

        print("\n\n\n" + '=' * 70 + "\n\n\n")
        for data_extra in manager.get_extras():
            print("EXTRAS:")
            print(data_extra)
            print("\n" + "*" * 70 + "\n")
