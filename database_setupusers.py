from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))




class Bookstore(Base):
    __tablename__ = 'bookstore'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'user_id' : self.user_id
        }




class BookGenre(Base):
    __tablename__ = 'book_genre'

    genre = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    title = Column(String(250))
    autor = Column(String(250))
    bookimage = Column(String(250))
    description = Column(String(250))
    price = Column(String(8))
    bookstore_id = Column(Integer, ForeignKey('bookstore.id'))
    bookstore = relationship(Bookstore) 
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


    
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'genre': self.genre,            
            'id': self.id,
            'title': self.title,
            'autor': self.autor,
            'bookimage': self.bookimage,
            'description': self.description,
            'price': self.price,

        }




engine = create_engine('sqlite:///book.db')

Base.metadata.create_all(engine)


