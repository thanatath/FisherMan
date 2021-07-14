#! /usr/bin/env python3

import datetime
from argparse import ArgumentParser
from base64 import b64decode
from os import path, walk, remove, getcwd
from re import findall
from subprocess import getoutput
from zipfile import ZipFile, ZIP_DEFLATED

import selenium.common.exceptions
from requests import get
from selenium.webdriver import Firefox, FirefoxOptions, FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from src.form_text import color_text
from src.logo import name

module_name = 'FisherMan: Extract information from facebook profiles.'
__version__ = "3.2.0"


class Fisher:
    def __init__(self):
        parser = ArgumentParser(description=f'{module_name} (Version {__version__})')
        exclusive_group = parser.add_mutually_exclusive_group()

        parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}',
                            help='Shows the current version of the program.')

        exclusive_group.add_argument('-u', '--username', action='store', nargs='+', required=False,
                                     type=str, help='Defines one or more users for the search.')

        exclusive_group.add_argument('--use-txt', action='store', required=False, dest='txt', metavar='TXT_FILE',
                                     type=str, nargs=1,
                                     help='Replaces the USERNAME parameter with a user list in a txt.')

        exclusive_group.add_argument("-i", "--id", action="store", nargs="+", required=False, type=str,
                                     help="Set the profile identification number.")

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
                            help="Returns extra data like profile picture, number of followers and friends. "
                                 "Depending on your machine, there may be a delay in executing the code.")

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

        print(color_text('blue', name))
        self.args = parser.parse_args()


class Manager:
    def __init__(self):
        self.__url__ = 'https://facebook.com/'
        self.__id_url_prefix__ = "https://www.facebook.com/profile.php?id="
        self.__prefix_url_search__ = "https://www.facebook.com/search/people/?q="  # coming soon...
        self.__fake_email__ = 'submarino.sub.aquatico@outlook.com'
        self.__password__ = 'MDBjbGVwdG9tYW5pYWNvMDA='
        self.__data__ = {}
        self.__affluent__ = {}
        self.__extras__ = {}

    def clean_all(self):
        """
            Clear all data.
        """
        self.__data__.clear()
        self.__affluent__.clear()
        self.__extras__.clear()

    def clean_data(self):
        """
            Clear dict data.
        """
        self.__data__.clear()

    def clean_affluent(self):
        """
            Clear affluent data.
        """
        self.__affluent__.clear()

    def clean_extras(self):
        """
            Clear extras data.
        """
        self.__extras__.clear()

    def set_email(self, string: str):
        """
            Defines the default email to use.

            :param string: Email.
        """
        self.__fake_email__ = string

    def set_pass(self, string: str):
        """
            Defines the default password to use.

            :param string: Password.
        """
        self.__password__ = string

    def set_data(self, dictionary: dict):
        """
            Updates the data in __date__ in its entirety.

            :param dictionary: dict to update.
        """
        self.__data__ = dictionary

    def set_affluent(self, dictionary: dict):
        """
            Updates the data in __affluent__ in its entirety.

            :param dictionary: dict to update.
        """
        self.__affluent__ = dictionary

    def set_extras(self, dictionary: dict):
        """
            Updates the data in __extras__ in its entirety.

            :param dictionary: dict to update.
        """
        self.__extras__ = dictionary

    def add_data(self, key, item):
        """
            Add a data in __date__ with an identifying key.

            :param key: identification key.
            :param item: data to be assigned to key.
        """
        self.__data__[key] = item

    def add_affluent(self, key, item):
        """
            Add a data in __affluent__ with an identifying key.

            :param key: identification key.
            :param item: data to be assigned to key.
        """
        self.__affluent__[key] = item

    def add_extras(self, key, item):
        """
            Add a data in __extras__ with an identifying key.

            :param key: identification key.
            :param item: data to be assigned to key.
        """
        self.__extras__[key] = item

    def get_url(self):
        """
            Returns default class page.

            :return: default page.
        """
        return self.__url__

    def get_id_prefix(self):
        """
            Returns user id link prefix.

            :return: link prefix
        """
        return self.__id_url_prefix__

    def get_email(self):
        """
            Returns default class email.

            :return: default email.
        """
        return self.__fake_email__

    def get_pass(self):
        """
            Returns default class password.

            :return: default password.
        """
        return self.__password__

    def get_data(self):
        """
            Returns all datas.

            :return: __data__.
        """
        return self.__data__

    def get_affluent(self):
        """
            Returns all affluents.

            :return: __affluent__.
        """
        return self.__affluent__

    def get_extras(self):
        """
            Returns all extras.

            :return: __extras__.
        """
        return self.__extras__

    def get_all_keys(self):
        """
            Return all keys from all dictionaries.

            extras, affluent, data
            To get all returns:
            datas = self.get_all_keys()

            For an individual:
            data = self.get_all_keys()[1]
        """
        return self.__extras__.keys(), self.__affluent__.keys(), self.__data__.keys()

    def get_all_items(self):
        """
            Return all items from all dictionaries.

            extras, affluent, data
            To get all returns:
            datas = self.get_all_items()

            For an individual:
            data = self.get_all_items()[1]
        """
        return self.__extras__.items(), self.__affluent__.items(), self.__data__.items()


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
                if (extension.lower() == ".txt" and _file_name != "requeriments") or extension.lower() == ".jpeg":
                    zip_output.write(archive)
                    remove(archive)
    print(f'[{color_text("green", "+")}] successful compression')


manager = Manager()


def extra_data(parse, brw: Firefox, user: str):
    """
        Save other data outside the about user page.

        :param parse: ArgParse instance namespace arguments to change code flow.
        :param brw: Instance of WebDriver.
        :param user: username to search.
    """
    brw.get(f"{manager.get_url() + user}")

    _xpath_img = '//*[@id="mount_0_0_qn"]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[2]/div/div/' \
                 'div[1]/div/div/div/a/div/svg/g/image'

    _xpath_follow = '//*[@id="mount_0_0_qn"]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[1]/div/' \
                    'div/div/div/div/div/div/div[1]/div[2]/div/div[2]/span/span/a'

    _xpath_friend = '/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[3]/div/div/div/div[1]' \
                    '/div/div/div[1]/div/div/div/div/div/div/a[3]/div[1]/span'

    # profile image collection
    try:
        img = WebDriverWait(brw, 10).until(ec.visibility_of_element_located((By.XPATH, _xpath_img)))
    except selenium.common.exceptions.NoSuchElementException:
        print(f'[{color_text("yellow", "-")}] non-existent element')
    except selenium.common.exceptions.TimeoutException:
        if parse.verbose:
            print(f'[{color_text("yellow", "-")}] timed out to get the profile image')
        else:
            print(f'[{color_text("yellow", "-")}] time limit exceeded')
    else:
        out = getoutput(f"wget {img}")
        if "403: Forbidden" in out:
            print(f'[{color_text("red", "-")}] ERROR 403: Forbidden. Unable to download profile picture')
        else:
            print(f'[{color_text("green", "+")}] downloaded profile picture')

    # follower collection
    try:
        WebDriverWait(brw, 10).until(ec.visibility_of_element_located((By.XPATH, _xpath_follow)))
    except selenium.common.exceptions.NoSuchElementException:
        print(f'[{color_text("yellow", "-")}] non-existent element')
        followers = None
    except selenium.common.exceptions.TimeoutException:
        if parse.verbose:
            print(f'[{color_text("yellow", "-")}] timed out to get the followers')
        else:
            print(f'[{color_text("yellow", "-")}] time limit exceeded')
        followers = None
    else:
        followers = brw.find_element_by_xpath(_xpath_follow).text

    # friends collection
    try:
        WebDriverWait(brw, 10).until(ec.visibility_of_element_located((By.XPATH, _xpath_friend)))
    except selenium.common.exceptions.NoSuchElementException:
        print(f'[{color_text("yellow", "-")}] non-existent element')
        friends = None
    except selenium.common.exceptions.TimeoutException:
        if parse.verbose:
            print(f'[{color_text("yellow", "-")}] timed out to get the friends')
        else:
            print(f'[{color_text("yellow", "-")}] time limit exceeded')
        friends = None
    else:
        # the return is a string containing both the word "friends" and the number of friends
        # this IF is to not only return the pure word
        temp = brw.find_element_by_xpath(_xpath_friend).text
        if len(temp) > 6 and len(temp) > 7:
            friends = temp
        else:
            friends = None

    if parse.txt:
        _file_name = rf"extraData-{user}-{str(datetime.datetime.now())[:16]}.txt"
        if parse.compact:
            _file_name = f"extraData-{user}.txt"
        with open(_file_name, "w+") as extra:
            extra.write(followers)
            extra.write(friends)
    else:
        # in the future to add more data variables, put in the list
        manager.add_extras(user, [followers, friends])


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
    for usrs in items:
        if usrs.isnumeric():
            prefix = manager.get_id_prefix()
            for C, bn in enumerate(branch):
                branch[C] = bn.replace("/", "&sk=")
        else:
            prefix = manager.get_url()
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

        for bn in branch:
            brw.get(f'{prefix + usrs + bn}')
            try:
                output = WebDriverWait(brw, 10).until(ec.presence_of_element_located((By.CLASS_NAME, 'f7vcsfb0')))
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
            div = "\n\n\n" + '=' * 70 + "\n\n\n"
            bar = "\n" + "*" * 70 + "\n"

            for memb in manager.get_affluent()[usrs]:
                print()
                print(f'[{color_text("white", "*")}] Coming in {memb}')
                temp_data.append(div)

                # search for extra data
                if parse.several:
                    if parse.verbose:
                        print(f'[{color_text("blue", "+")}] getting extra data...')
                    extra_data(parse, brw, memb)

                for bn in branch:
                    brw.get(f'{memb + bn}')
                    try:
                        output2 = WebDriverWait(brw, 10).until(ec.presence_of_element_located((By.CLASS_NAME,
                                                                                               'f7vcsfb0')))
                    except Exception as error:
                        print(f'[{color_text("red", "-")}] class f7vcsfb0 did not return')
                        if parse.verbose:
                            print(color_text("yellow", f"error details:\n{error}"))
                    else:
                        if parse.verbose:
                            print(f'[{color_text("blue", "+")}] Collecting data from: div.f7vcsfb0')
                        else:
                            print(f'[{color_text("blue", "+")}] collecting data ...')
                        temp_data.append(output2.text + bar)

            # add a bar to separate between users
            temp_data.append(div)
        # complete addition of all data
        manager.add_data(usrs, temp_data)


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


def main(parse):
    """
        Main function.

        :param parse: ArgParse instance namespace arguments to change code flow.

        Where the other functions and flow decisions are executed.
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
    _options.add_argument('--profile-directory=Default')
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
        browser = Firefox(**configs)
    except Exception as error:
        print(color_text("red",
                         f'The executable "geckodriver" was not found or the browser "Firefox" is not installed.'))
        print(color_text("yellow", f"error details:\n{error}"))
    else:
        # others arguments
        browser.delete_all_cookies()

        login(parse, browser)
        if parse.txt:
            scrape(parse, browser, upload_txt_file(parse.txt))
        elif parse.username:
            scrape(parse, browser, parse.username)
        elif parse.id:
            scrape(parse, browser, parse.id)
        browser.quit()


if __name__ == '__main__':
    fs = Fisher()
    update()
    main(fs.args)
    txt_file = fs.args.txt
    print()

    if fs.args.out:  # .txt output creation
        if fs.args.username is None:
            for usr in upload_txt_file(txt_file):
                file_name = rf"{usr}-{str(datetime.datetime.now())[:16]}.txt"
                if fs.args.compact:
                    file_name = usr + ".txt"
                with open(file_name, 'a+') as file:
                    for data_list in manager.get_data()[usr]:
                        file.writelines(data_list)

        else:
            for usr2 in fs.args.username:
                file_name = rf"{usr2}-{str(datetime.datetime.now())[:16]}.txt"
                if fs.args.compact:
                    file_name = usr2 + ".txt"
                with open(file_name, 'a+') as file:
                    for data_list in manager.get_data()[usr2]:
                        file.writelines(data_list)

        print(f'[{color_text("green", "+")}] .txt file(s) created')
        if fs.args.compact:
            if fs.args.verbose:
                print(f'[{color_text("white", "*")}] preparing compaction...')
            compact()

    else:
        print(color_text('green', 'Information found:'))
        print('-' * 60)
        for profile in manager.get_all_keys()[2]:
            for data in manager.get_data()[profile]:
                print(data)
                print()
                print('-' * 60)

            if fs.args.several:
                print("EXTRAS:")
                for data_extra in manager.get_extras()[profile]:
                    print(data_extra)
