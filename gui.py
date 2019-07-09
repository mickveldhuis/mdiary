import urwid
from configparser import ConfigParser
import argparse
from pathlib import Path

PALETTE = [
    ('edit_body', 'black', 'light green'),
    ('body', 'white', 'black'),
    ('footer', 'white', 'black', 'bold'),
    ('header', 'white', 'black', 'bold'),
    ('container', 'white', 'black'),
    ('button', 'white', 'black')
]

class MainView(urwid.WidgetWrap):
    """
        Class responsible for providing the main application window.
    """
    def __init__(self, controller):
        self.controller = controller
        urwid.WidgetWrap.__init__(self, self.window())

    def window(self):
        div = urwid.Divider()
        div_bar = urwid.Divider('-')

        # Header
        hd_txt = urwid.Text(u'mDiary: A Simple Diary Application', align='center')
        header = urwid.Columns([div_bar, hd_txt, div_bar])
        header = urwid.AttrMap(header, 'header')

        # Body
        self.edit_field = urwid.Edit(multiline=True)
        body = urwid.AttrMap(self.edit_field, 'edit_body')
        body = urwid.LineBox(body, title='New page:')

        # Footer
        btn_quit = urwid.Button(('button', u'Quit'), self.on_quit)
        btn_save = urwid.Button(('button', u'Save & Exit'), self.on_save)
        btn_append = urwid.Button(('button', u'Add to diary'), self.on_append)

        footer = urwid.Columns([btn_append, div, btn_save, div, btn_quit])
        footer = urwid.AttrMap(footer, 'footer')

        # Container
        pile = urwid.Pile([header, div, body, div, footer])
        view = urwid.Filler(pile, valign='top')
        view = urwid.AttrMap(view, 'container')

        return view

    def quit_program(self):
        raise urwid.ExitMainLoop()
    
    def on_save(self, button):
        txt = self.edit_field.get_text()[0]

        file = open('current_.txt', 'w')
        file.write(txt)
        file.close()

        self.quit_program()

    def on_quit(self, button):
        self.quit_program()

    def on_append(self, button):
        txt = self.edit_field.get_text()[0]
        self.edit_field.set_edit_text(u'')
        
        file = open('current_.txt', 'w')
        file.write(txt)
        file.close()

class InitView(urwid.WidgetWrap):
    """
        Class responsible for providing the initialization window.
    """
    def __init__(self, controller):
        self.controller = controller
        urwid.WidgetWrap.__init__(self, self.window())

    def window(self):
        div = urwid.Divider()
        div_bar = urwid.Divider('-')

        self.info = urwid.Text(u'')
        self.edit = urwid.Edit(u'(1) Diary name: ')

        self.radio_group = []
        self.yes = urwid.RadioButton(self.radio_group, u'Yes', state=False, on_state_change=self.on_radio_change)
        self.no = urwid.RadioButton(self.radio_group, u'No', state=True)

        listbox_content = [
            urwid.Text(u'In order to use the diary you should specify a few parameters,'),
            div,
            self.edit,
            div,
            urwid.Text(u'(2) Do you want to use a key? (For extra security)'),
            div,
            urwid.Columns([
                urwid.Padding(urwid.GridFlow([self.yes, self.no], 10, 3, 1, 'left'), left=4, right=3, min_width=10),
                self.info]),
            div,
            urwid.Columns([
                urwid.Padding(urwid.Button(('button', u'Confirm & to diary'), self.on_confirm_continue),
                            align='center', width=('relative', 90)),
                urwid.Padding(urwid.Button(('button', u'Confirm & Quit'), self.on_confirm_quit), 
                            align='center', width=('relative', 90)),
                urwid.Padding(urwid.Button(('button', u'Quit'), self.on_quit), 
                            align='center', width=('relative', 90))
            ])
        ]

        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(listbox_content))
        view = urwid.AttrMap(listbox, 'body')
        view = urwid.LineBox(view, title='Setup Menu')

        return view

    def on_radio_change(self, radio_button, new_state):
        if new_state:
            self.info.set_text(u'Your key will be stored at ~/.mdiary/<diary name>.key (Keep it safe!)')
        else:
            self.info.set_text(u'')

    def confirm_config(self):
        db_name = self.edit.get_edit_text().strip()
        using_key = 'false'

        if db_name:
            if self.yes.state:
                using_key = 'true'
            
            self.controller.gen_config(db_name, using_key)

    def quit_program(self):
        raise urwid.ExitMainLoop()

    def on_confirm_quit(self, button):
        self.confirm_config()
        self.quit_program()

    def on_quit(self, button):
        self.quit_program()

    def on_confirm_continue(self, button):
        self.confirm_config()
        self.controller.set_state('main')

class Diary:
    """
        Class controlling the behaviour of the application,
        handling the views etc.
    """
    CONFIG_FILE = 'mdiary.conf'

    def __init__(self):
        self.states = {
            'init': InitView(self),
            'main': MainView(self),
            'errs': None
        }

        self.view = self.states['main']
        self.config = ConfigParser()

    def main(self):
        # parser = argparse.ArgumentParser(description='A simple terminal diary, written in Python, with encryption possibilities.')
        # parser.add_argument('--key', '-k', help='Diary safety key!',
        #                     action='store', dest='key')
        # parser.add_argument('--version', '-v', action='version', version='mdiary 0.0.1')
        # parser_results = parser.parse_args()

        # ifs self.get_config().using_key and parser_results.key:
        #     self.key_file = parser_results.key
        # elif self.get_config().using_key and not parser_results.key:
        #     print('Use your key to get access to the diary by using the [--key, -k KEY] argument!')
        #     sys.exit()

        if not Path(Diary.CONFIG_FILE).is_file():
            self.view = self.set_state('init')
        
        self.loop = urwid.MainLoop(self.view,  PALETTE)
        self.loop.run()

    def set_state(self, state):
        if state == 'main':
            self.view = self.states['main']
        elif state == 'init':
            self.view = self.states['init']
        # elif state == 'errs':
        #     self.view = self.states['errs']

    def gen_config(self, db_name, using_key):
        self.config['settings'] = {
            'db': db_name + '.db',
            'using_key': using_key
        }

        with open(Diary.CONFIG_FILE, 'w') as f:
            self.config.write(f)
    
    def get_config(self):
        self.config.read(Diary.CONFIG_FILE)
        conf = {
            'db': self.config.get('setting', 'db'),
            'using_key': self.config.getboolean('setting', 'using_key')
        }

        return conf


def main():
    diary = Diary()
    diary.main()

if __name__ == '__main__':
    main()