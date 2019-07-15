import sys
import urwid
from configparser import ConfigParser
import argparse
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from diary_db import DBHandler


def to_file(txt, fn='_output.txt'):
    """
        Writes the string txt to a file.
        (This function ONLY exists for debugging
         purposes, and will soon be deleted...)
    """
    file = open(fn, 'w+')
    file.write(txt)
    file.close()

PALETTE = [
    ('edit_body', 'black', 'light green'),
    ('body', 'white', 'black'),
    ('footer', 'white', 'black', 'bold'),
    ('header', 'white', 'black', 'bold'),
    ('container', 'white', 'black'),
    ('button', 'white', 'black')
]

class BaseView(urwid.WidgetWrap):
    def __init__(self, controller):
        self.controller = controller
        urwid.WidgetWrap.__init__(self, self.window())
    
    def window(self):
        pass
    
    def on_quit(self, button):
        self.controller.quit_program()

class InitView(BaseView):
    """
        Class responsible for providing the initialization window.
    """
    def __init__(self, controller):
        super().__init__(controller)

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

            key_loc = Path('~/.mdiary') / (db_name + '.key')
            key_loc = key_loc.expanduser()

            self.controller.gen_key(key_loc)

    def on_confirm_quit(self, button):
        self.confirm_config()
        self.quit_program()

    def on_confirm_continue(self, button):
        self.confirm_config()
        self.controller.set_view('menu')

class MenuView(BaseView):
    """
        Class responsible for providing the menu window.
    """
    def __init__(self, controller):
        super().__init__(controller)

    def window(self):
        div = urwid.Divider()
        div_bar = urwid.Divider('-')

        listbox_content = [
            div,
            urwid.Padding(urwid.Button(('button', u'New entry'), self.on_to_writer),
                          align='center', width=('relative', 50)),
            urwid.Padding(urwid.Button(('button', u'View entries'), self.on_to_reader), 
                          align='center', width=('relative', 50)),
            urwid.Padding(urwid.Button(('button', u'Quit'), self.on_quit), 
                           align='center', width=('relative', 50)),
            div
        ]

        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(listbox_content))
        view = urwid.AttrMap(listbox, 'body')
        view = urwid.LineBox(view, title='mDiary: Menu')

        return view

    def on_to_writer(self, button):
        self.controller.set_view('writer')

    def on_to_reader(self, button):
        self.controller.set_view('reader')

class WriterView(BaseView):
    """
        Class responsible for providing the application 
        window handling the creation of new entries.
    """
    def __init__(self, controller):
        super().__init__(controller)

    def window(self):
        div = urwid.Divider()
        
        self.edit_field = urwid.Edit(multiline=True)
        edit_box = urwid.AttrMap(self.edit_field, 'edit_body')
        edit_box = urwid.LineBox(edit_box, title='New page:')

        btn_quit = urwid.Button(('button', u'Quit'), self.on_quit)
        btn_save = urwid.Button(('button', u'Save & Exit'), self.on_save)
        btn_append = urwid.Button(('button', u'Add to diary'), self.on_append)
        btn_menu = urwid.Button(('button', u'To menu'), self.on_to_menu)

        listbox_content = [
            div,
            urwid.Padding(edit_box, align='center', width=('relative', 90)),
            div,
            urwid.Padding(urwid.Columns([
                urwid.Padding(btn_append, align='center', width=('relative', 80)),
                urwid.Padding(btn_save, align='center', width=('relative', 80)),
                urwid.Padding(btn_menu, align='center', width=('relative', 80)),
                urwid.Padding(btn_quit, align='center', width=('relative', 80))
            ]), align='center', width=('relative', 90)),
        ]

        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(listbox_content))
        view = urwid.AttrMap(listbox, 'body')
        view = urwid.LineBox(view, title='mDiary: New Entry')

        return view

    def on_save(self, button):
        txt = self.edit_field.get_text()[0]

        if self.controller.is_using_key():
            txt = self.controller.encrypt_entry(txt)
        
        self.controller.db_handler.new_entry(txt)
        self.quit_program()
    
    def on_to_menu(self, button):
        self.controller.set_view('menu')

    def on_append(self, button):
        txt = self.edit_field.get_text()[0]
        self.edit_field.set_edit_text(u'')

        if self.controller.is_using_key():
            txt = self.controller.encrypt_entry(txt)

        self.controller.db_handler.new_entry(txt)

class EditView(BaseView):
    """
        Class responsible for providing the application 
        window handling the creation of new entries.
    """
    def __init__(self, controller):
        self.id = None
        super().__init__(controller)

    def window(self):
        div = urwid.Divider()
        
        self.edit_field = urwid.Edit(multiline=True)
        input_field = urwid.LineBox(urwid.AttrMap(self.edit_field, 'edit_body'))

        self.edit_info = urwid.Text(u'')

        listbox_content = [
            div,
            urwid.Padding(self.edit_info, align='center', width=('relative', 90)),
            div,
            urwid.Padding(input_field, align='center', width=('relative', 90)),
            div,
            urwid.Columns([
                urwid.Padding(urwid.Button(('button', u'Save changes'), self.on_save),
                            align='center', width=('relative', 80)),
                urwid.Padding(urwid.Button(('button', u'Cancel'), self.on_cancel), 
                            align='center', width=('relative', 80)),
                urwid.Padding(urwid.Button(('button', u'Quit'), self.on_quit), 
                            align='center', width=('relative', 80))
            ]),
        ]

        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(listbox_content))
        view = urwid.AttrMap(listbox, 'body')
        view = urwid.LineBox(view, title='mDiary: Edit entry {}'.format(self.id))

        return view
    
    def set_state(self, id):
        self.id = id

        entry = self.controller.db_handler.get_entry(self.id)
        entry_text = entry.entry_text

        if self.controller.is_using_key():
            entry_text = self.controller.decrypt_entry(entry_text)

        self.edit_field.edit_text = entry_text
        info = u'Editting entry {}. Originally created on {}-{}-{}.'.format(self.id, entry.timestamp.year, 
                                                                            entry.timestamp.month, 
                                                                            entry.timestamp.day)
        self.edit_info.set_text(info)
        

    def on_save(self, button):
        if self.id:
            txt = self.edit_field.get_text()[0]
            
            if self.controller.is_using_key():
                txt = self.controller.encrypt_entry(txt)
            
            self.controller.db_handler.update_entry(self.id, txt)
        
        self.controller.set_view('reader')
    
    def on_cancel(self, button):
        self.controller.set_view('reader')

class ReaderView(BaseView):
    """
        Class responsible for providing the application window
        handling the displaying / deleting of entries.
    """
    def __init__(self, controller):
        super().__init__(controller)
    
    def window(self):
        div = urwid.Divider()

        menu_btn = urwid.Button(u'To menu', self.on_to_menu)
        quit_btn = urwid.Button(('button', u'Quit'), self.on_quit)

        col = urwid.Columns([
            urwid.Padding(menu_btn, align='center', width=('relative', 50)), 
            urwid.Padding(quit_btn, align='center', width=('relative', 50))
        ])

        listbox_content = [col, div]

        for entry in self.controller.db_handler.get_entries():
            entry_text = entry['entry_text']

            if self.controller.is_using_key():
                entry_text = self.controller.decrypt_entry(entry_text)

            entry_box = self.gen_entry(entry['entry_id'], entry['timestamp'], entry_text)
            listbox_content += [entry_box, div]

        listbox_content += [col]
        
        self.walker = urwid.SimpleFocusListWalker(listbox_content)
        self.listbox = urwid.ListBox(self.walker)

        view = urwid.AttrMap(self.listbox, 'body')
        view = urwid.LineBox(view, title='mDiary: Entry Browser')
        to_file(type(view).__name__)
        return view

    def gen_entry(self, id, date, txt):
        """
            Returns a listbox containing the information about diary entries.
        """
        div = urwid.Divider()
        div_bar = urwid.Divider('-')

        pile = urwid.Pile([
            div,
            urwid.Padding(urwid.Text(txt), align='center', width=('relative', 90)),
            div,
            div_bar,
            div,
            urwid.Columns([
                urwid.Padding(urwid.Button(u'Delete entry', self.on_delete, id),
                              align='center', width=('relative', 40)),
                urwid.Padding(urwid.Button(u'Update entry', self.on_update, id),
                              align='center', width=('relative', 40))
            ]),
            div,
        ])
        
        pile = urwid.AttrMap(pile, 'body')
        entry_lb = urwid.Padding(urwid.LineBox(pile, title='Entry no. {} on {}-{}-{} ({}:{})'.format(
                                 id, date.year, date.month, date.day, date.hour, date.minute)), 
                                 align='center', width=('relative', 80))

        return entry_lb

    def on_to_menu(self, button):
        self.controller.set_view('menu')

    def on_delete(self, button, id):
        self.controller.db_handler.remove_entry(id)

        _, index = self.listbox.get_focus()
        del self.walker[index:index+2] # Update the view and delete a divider
    
    def on_update(self, button, id):
        self.controller.views['edit'].set_state(id)
        self.controller.set_view('edit')

class Diary:
    """
        Class controlling the behaviour of the application,
        handling the views etc.
    """

    def __init__(self):
        self.config_path = Path.home() / '.config' / 'mdiary'
        self.config_file = self.config_path / 'mdiary.conf'
        self.config = ConfigParser()
        self.db_handler = None
        self.key_file = None
        self.key = None

        self.views = {
            'init': InitView(self),
            'writer': WriterView(self),
            'menu': MenuView(self),
            'edit': EditView(self)
        }

    def main(self):
        """
            The main function.
        """
        if not self.config_path.is_dir():
            self.config_path.mkdir(exist_ok=True)

        parser = argparse.ArgumentParser(description='A simple terminal diary, written in Python, with encryption possibilities.')
        parser.add_argument('--key', '-k', help='Diary safety key!',
                            action='store', dest='key')
        parser.add_argument('--reset', '-r', help='Reset the configuration file.',
                        action='store_true', dest='reset')
        parser.add_argument('--version', '-v', action='version', version='mdiary 0.0.2')
        parser_results = parser.parse_args()
 
        if parser_results.reset and self.config_file.is_file():
            self.reset_config()

        if not self.config_file.is_file():
            init_view = self.views['init']
        else:
            if self.is_using_key() and parser_results.key:
                self.key_file = Path(parser_results.key).expanduser()
                self.set_key()
            elif self.is_using_key() and not parser_results.key:
                print('Use your key to get access to the diary by using the [--key, -k KEY] argument!')
                sys.exit()
            
            init_view = self.views['menu']
            self.gen_db()

        self.loop = urwid.MainLoop(init_view, PALETTE)
        self.loop.run()

    def set_view(self, id='menu'):
        """
            Set the view to either 'writer', 'reader', 'menu' or 'init'.
        """
        if id == 'reader':
            self.loop.widget = ReaderView(self)
        else:
            self.loop.widget = self.views[id]

    def gen_config(self, db_name, using_key):
        """
            Generate an ini like configuration file with
            parameters 'db' for the database name and location, 
            and 'using_key' which stores True/False depending
            on whether one want to use a secret key to encrypt 
            the diary entries (functionality nog yet implemented!).
        """
        self.config['settings'] = {
            'db': db_name + '.db',
            'using_key': using_key
        }

        with self.config_file.open(mode='w') as f:
            self.config.write(f)
        
        self.gen_db()

    def get_config(self):
        """
            Returns the retrieved configuration file's contents.
        """
        self.config.read(self.config_file)
        conf = {
            'db': self.config.get('settings', 'db'),
            'using_key': self.config.getboolean('settings', 'using_key')
        }

        return conf

    def reset_config(self):
        """
            Resets the configuration file such that one can initiate
            a new database, key, etc.
        """
        suffix = '.old'
        file_old = self.config_path / ('mdiary.conf' + suffix)
        
        while True: 
            if not file_old.is_file():
                break

            suffix += '.old'
            file_old = self.config_path / ('mdiary.conf' + suffix)

        self.config_file.rename(file_old)
        
    def gen_db(self):
        if self.get_config()['db']:
            self.db_handler = DBHandler(name=self.get_config()['db'])
            self.db_handler.create()
            self.db_handler.new_session()
    
    def gen_key(self, key_fn):
        """
            Generates a key at the <Path> key_fn.
        """
        self.key_file = key_fn

        if self.key_file:
            self.key_file.touch()
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)

            self.set_key()
        else:
            raise AttributeError('self.key_file does not exist, SET IT IDIOT!')
        
    def set_key(self):
        if self.key_file.is_file():
            key = self.key_file.read_bytes()
            self.key = key
        else:
            raise AttributeError('The key_file attribute is not valid or does not exist!')
    
    def encrypt_entry(self, text):
        f = Fernet(self.key)
        enc = f.encrypt(text.encode())

        return enc
    
    def decrypt_entry(self, enc_text):
        f = Fernet(self.key)

        try:
            dec = f.decrypt(enc_text)
        except InvalidToken:
            self.quit_program()

        return dec.decode()
    
    def is_using_key(self):
        return self.get_config()['using_key']
    
    def close_diary(self):
        self.db_handler.close()
    
    def quit_program(self):
        raise urwid.ExitMainLoop()
