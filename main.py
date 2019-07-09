import sys
import urwid
import pickle
import argparse

CONFIG = 'mdiary.conf'
KEY_FILE = None

def gen_config(db_name, secured):
    config = {
        db: db_name,
        using_key = secured
    }

    pickle.dump(config, open(CONFIG, 'wb'))

def get_config():
    config = pickle.load(open(CONFIG, 'rb'))

    return config

def main():
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A simple terminal diary, written in Python, with encryption possibilities.')
    parser.add_argument('--key', '-k', help='Diary safety key!',
                        action='store', dest='key')
    parser.add_argument('--version', '-v', action='version', version='mdiary 0.0.1')
    p_res = parser.parse_args()

    if get_config().using_key and p_res.key:
        KEY_FILE = p_res.key
    elif get_config().using_key and not p_res.key:
        print('Use your key to get access to the diary by using the --key KEY argument!')
        sys.exit()
    
    main()