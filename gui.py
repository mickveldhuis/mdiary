import urwid

def key_handler(key):
    if input in ('Q', 'q'):
        raise urwid.ExitMainLoop()

palette = [
    ('body', 'black', 'light green'),
    ('footer', 'white', 'black', 'bold'),
    ('header', 'white', 'black', 'bold'),
    ('container', 'white', 'black'),
    ('button', 'white', 'black')
]

div = urwid.Divider()
div_bar = urwid.Divider('-')

btn_quit = urwid.Button(('button', u'Quit'))
btn_save = urwid.Button(('button', u'Save & Exit'))
btn_append = urwid.Button(('button', u'Add to diary')) # Does not close the entry, solely stores it and deletes i

# HEADER
hd_txt = urwid.Text(u'mDiary: A Simple Diary Application', align='center')
header = urwid.Columns([div_bar, hd_txt, div_bar])
header = urwid.AttrMap(header, 'header')

# BODY
edit_entry = urwid.Edit(multiline=True)
txt_box = urwid.AttrMap(edit_entry, 'body')
body = urwid.LineBox(txt_box, title='New page:')

# FOOTER
ftr = urwid.Columns([btn_append, div, btn_save, div, btn_quit])
# ft_txt = urwid.Text(u'Q/q: Exit; S/s: Save & Exit')
footer = urwid.AttrMap(ftr, 'footer')

# CONTAINER
pile = urwid.Pile([header, div, body, div, footer])
view = urwid.Filler(pile, valign='top')
view = urwid.AttrMap(view, 'container')


# BUTTON LOGIC

def quit():
    raise urwid.ExitMainLoop()

def on_save(button):
    txt = edit_entry.get_text()[0]
    file = open('current.txt', 'w')
    file.write(txt)
    file.close()

    quit()

def on_quit(button):
    quit()

def on_append(button):
    txt = edit_entry.get_text()[0]
    edit_entry.set_edit_text(u'')
    file = open('current_.txt', 'w')
    file.write(txt)
    file.close()


urwid.connect_signal(btn_quit, 'click', on_quit)
urwid.connect_signal(btn_save, 'click', on_save)
urwid.connect_signal(btn_append, 'click', on_append)

urwid.MainLoop(view, palette, unhandled_input=key_handler).run()