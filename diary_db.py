from datetime import datetime
from sqlalchemy import (Table, Column, Integer, Numeric, String, 
                        Text, DateTime, create_engine, func)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

Base = declarative_base()

class Entry(Base):
    __tablename__ = 'entries'

    entry_id   = Column('id', Integer(), primary_key=True)
    entry_text = Column('text', Text(), nullable=False)
    timestamp  = Column('timestamp', DateTime(), nullable=False)
    
    def __repr__(self):
        return "Entry(text='{self.entry_text}', timestamp={self.timestamp})".format(self=self)

class DBHandler():
    def __init__(self, name='mdiary.db'):
        self.db_name = name
        self.db_path = Path.home() / '.mdiary'
        self.full_path = self.db_path / self.db_name  
        self.engine = None
        self.session = None

    def create(self):
        """
            Create a new database.
        """
        if not self.db_path.is_dir():
            self.db_path.mkdir(exist_ok=True)

        if not self.engine:
            self.engine = create_engine('sqlite:///{}'.format(self.full_path))
        
        Base.metadata.create_all(self.engine)
    
    def new_session(self):
        """
            Initialize a new session object.
        """
        if not self.session:
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
    
    def new_entry(self, txt):
        """
            Appends a new diary entry to the database,
            given the text of the entry.
        """
        dt = datetime.now()

        new_entry = Entry(entry_text=txt, timestamp=dt)

        self.session.add(new_entry)
        self.session.commit()
        
        return new_entry

    def get_entries(self):
        """
            Retrieve all diary entries as a list of dictionaries. 
        """
        entries = self.session.query(Entry).all()
        res = map(lambda q: q.__dict__, entries)
        
        return list(res)
    
    def get_entries_raw(self):
        """
            Returns all diary entries as a iterable of Entry objects.
        """
        entries = self.session.query(Entry)
        
        return entries

    def remove_entry(self, id):
        """
            Delete an entry given its id.
        """
        query = self.session.query(Entry).filter(Entry.entry_id == id)
        d_entry = query.one()
        self.session.delete(d_entry)
        self.session.commit()
    
    def entry_exists(self, id):
        """
            Returns True if the entry exists in the DB.
        """
        query = self.session.query(Entry.entry_id)
        query = query.filter_by(entry_id=id).scalar() 
        return query is not None

    # def update_entry(self, id, txt):
    #     """
    #         TODO (no priority) 
    #     """
    #     # Would look something like
    #       query = self.session.query(Entry)
    #       entry = query.filter(Entry.entry_id == id).first()
    #       entry.text = txt
    #       self.session.commit()
    #       return entry.text # Maybe not
    
    def get_entry_count(self):
        """
            Returns the number of entries stored in the database.
        """
        counter = self.session.query(func.count(Entry.entry_text).label('entry_count')).first()
        return counter.entry_count

    def close(self):
        self.session.close()