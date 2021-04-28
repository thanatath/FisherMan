#! /usr/bin/env python3

from selenium.webdriver import Firefox, FirefoxOptions
from time import sleep
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from requests import get
from re import findall
from form_text import *
from logo import *

module_name = 'FisherMan: Extract information from facebook profiles'
__version__ = "2.1"


class Fisher:
    def __init__(self):
        parser = ArgumentParser(description=f'{module_name} (Version {__version__})',
                                formatter_class=RawDescriptionHelpFormatter)

        parser.add_argument('USERSNAMES', action='store', nargs='+',
                            help='defines one or more users for the search')

        parser.add_argument('--version', action='version',
                            version=f'%(prog)s {__version__}', help='Shows the current version of the program.')

        parser.add_argument('--email', action='store', metavar='EMAIL', dest='email',
                            required=False,
                            help='If the profile is blocked, you can define your account, '
                                 'however you have the search user in your friends list.')

        parser.add_argument('--password', action='store', metavar='PASSWORD', dest='pwd',
                            required=False,
                            help='Set the password for your facebook account, '
                                 'this parameter has to be used with --email.')

        parser.add_argument('--browser', '-b', action='store_true', dest='browser',
                            required=False,
                            help='Opens the browser / bot')

        parser.add_argument('--use-txt', action='store', required=False, dest='txt', metavar='TXT_FILE',
                            help='Replaces the USERSNAMES parameter with a user list in a txt')

        parser.add_argument('--file-output', '-o', action='store_true', required=False, dest='out',
                            help='Save the output data to a .txt file')

        parser.add_argument('--verbose', '-v', '-d', '--debug', action='store_true', required=False, dest='verb',
                            help='It shows in detail the data search process')

        self.args = parser.parse_args()
        self.site = 'https://facebook.com/'
        self.__fake_email__ = 'submarino.sub.aquatico@outlook.com'
        self.__password__ = '0cleptomaniaco0'
        self.data = []
        print(color_text('white', name))

    @staticmethod
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

    def get_data(self):
        return self.data

    def upload_txt_file(self):
        try:
            with open(self.args.txt, 'r') as txt:
                users_txt = txt.readlines()
        except Exception as error:
            print(color_text('red', f'An error has occurred: {error}'))
        else:
            return users_txt

    def run(self):
        if not self.args.browser:
            if self.args.verb:
                print(f'[ {color_text("blue", "*")} ] Starting in hidden mode')
            options = FirefoxOptions()
            options.add_argument("--headless")
            navegador = Firefox(options=options)
        else:
            if self.args.verb:
                print(f'[ {color_text("white", "*")} ] Opening browser ...')
            navegador = Firefox()
        navegador.get(self.site)

        email = navegador.find_element_by_name("email")
        pwd = navegador.find_element_by_name("pass")
        ok = navegador.find_element_by_name("login")
        classes = ['f7vcsfb0', 'discj3wi']

        email.clear()
        pwd.clear()
        if self.args.email is None or self.args.pwd is None:
            if self.args.verb:
                print(f'[ {color_text("white", "*")} ] adding email: {self.__fake_email__}')
                email.send_keys(self.__fake_email__)
                print(f'[ {color_text("white", "*")} ] adding pasword...')
                pwd.send_keys(self.__password__)
            else:
                print(f'[ {color_text("white", "*")} ] logging into the account: {self.__fake_email__}')
                email.send_keys(self.__fake_email__)
                pwd.send_keys(self.__password__)
        else:
            if self.args.verb:
                print(f'adding email: {self.args.email}')
                email.send_keys(self.args.email)
                print('adding pasword...')
                pwd.send_keys(self.args.pwd)
            else:
                print(f'logging into the account: {self.args.email}')
                email.send_keys(self.args.email)
                pwd.send_keys(self.args.pwd)
        ok.click()
        sleep(1)
        if self.args.verb:
            print(f'[ {color_text("green", "+")} ] successfully logged in')
        for usr in self.args.USERSNAMES:
            if ' ' in usr:
                usr = str(usr).replace(' ', '.')
            print(f'[ {color_text("white", "*")} ] Coming in {self.site + usr}')
            navegador.get(f'{self.site + usr}/about')

            sleep(3)
            for c in classes:
                try:
                    output = navegador.find_element_by_class_name(c)
                except Exception as error:
                    print(f'[ {color_text("red", "-")} ] class {c} did not return')
                    print(color_text('red', f'ERROR: {error}'))
                else:
                    if output:
                        if self.args.verb:
                            print(f'[ {color_text("blue", "+")} ] Collecting data from: div.{c}')
                        else:
                            print(f'[ {color_text("blue", "+")} ] collecting data ...')
                        self.data.append(output.text)
                    else:
                        continue
                sleep(1)
        navegador.quit()


fs = Fisher()
fs.update()
fs.run()
stuff = fs.get_data()
print()
if fs.args.out:
    with open('output.txt', 'w+') as file:
        for user in fs.args.USERSNAMES:
            file.write('Name and Bio:\n')
            file.write(stuff[1])
            file.write('\n')
            file.write('Overview:\n')
            file.write(stuff[0])
            file.write('\n\n')
    print(f'[ {color_text("green", "+")} ] SUCCESS')
else:
    print(color_text('green', 'Information found:'))
    print('-' * 60)
    print(f'Name and Bio:')
    print(stuff[1])
    print()
    print('Overview:')
    print(stuff[0])
