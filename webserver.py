from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

from database_setupusers import Base, Bookstore, BookGenre, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create session and connect to DB ##
engine = create_engine('sqlite:///book.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


class webServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            # Objective 3 Step 2 - Create /bookstores/new page
            if self.path.endswith("/bookstores/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += "<h1>Make a New Bookstore</h1>"
                output += "<form method = 'POST' enctype='multipart/form-data' action = '/bookstores/new'>"
                output += "<input name = 'newBookstoreName' type = 'text' placeholder = 'New Bookstore Name' > "
                output += "<input type='submit' value='Create'>"
                output += "</form></html></body>"
                self.wfile.write(output)
                return
            if self.path.endswith("/edit"):
                bookstoreIDPath = self.path.split("/")[2]
                myBookstoreQuery = session.query(Bookstore).filter_by(
                    id=bookstoreIDPath).one()
                if myBookstoreQuery:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = "<html><body>"
                    output += "<h1>"
                    output += myBookstoreQuery.name
                    output += "</h1>"
                    output += "<form method='POST' enctype='multipart/form-data' action = '/bookstores/%s/edit' >" % bookstoreIDPath
                    output += "<input name = 'newBookstoreName' type='text' placeholder = '%s' >" % myBookstoreQuery.name
                    output += "<input type = 'submit' value = 'Rename'>"
                    output += "</form>"
                    output += "</body></html>"

                    self.wfile.write(output)
            if self.path.endswith("/delete"):
                bookstoreIDPath = self.path.split("/")[2]

                myBookstoreQuery = session.query(Bookstore).filter_by(
                    id=bookstoreIDPath).one()
                if myBookstoreQuery:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = ""
                    output += "<html><body>"
                    output += "<h1>Are you sure you want to delete %s?" % myBookstoreQuery.name
                    output += "<form method='POST' enctype = 'multipart/form-data' action = '/bookstores/%s/delete'>" % bookstoreIDPath
                    output += "<input type = 'submit' value = 'Delete'>"
                    output += "</form>"
                    output += "</body></html>"
                    self.wfile.write(output)

            if self.path.endswith("/bookstores"):
                bookstores = session.query(Bookstore).all()
                output = ""
                # Objective 3 Step 1 - Create a Link to create a new bookstore
                output += "<a href = '/bookstores/new' > Make a New bookstores Here </a></br></br>"

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output += "<html><body>"
                for bookstore in bookstores:
                    output += bookstore.name
                    output += "</br>"
                    # Objective 2 -- Add Edit and Delete Links
                    # Objective 4 -- Replace Edit href

                    output += "<a href ='/bookstore/%s/edit' >Edit </a> " % bookstore.id
                    output += "</br>"
                    # Objective 5 -- Replace Delete href
                    output += "<a href ='/bookstores/%s/delete'> Delete </a>" % bookstore.id
                    output += "</br></br></br>"

                output += "</body></html>"
                self.wfile.write(output)
                return
        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    # Objective 3 Step 3- Make POST method
    def do_POST(self):
        try:
            if self.path.endswith("/delete"):
                bookstoreIDPath = self.path.split("/")[2]
                myBookstoreQuery = session.query(Bookstore).filter_by(
                    id=bookstoreIDPath).one()
                if myBookstoreQuery:
                    session.delete(myBookstoreQuery)
                    session.commit()
                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/bookstores')
                    self.end_headers()

            if self.path.endswith("/edit"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))

                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newBookstoreName')
                    bookstoreIDPath = self.path.split("/")[2]

                    myBookstoreQuery = session.query(Bookstore).filter_by(
                        id=bookstoreIDPath).one()

                    if myBookstoreQuery != []:
                        myBookstoreQuery.name = messagecontent[0]
                        session.add(myBookstoreQuery)
                        session.commit()
                        self.send_response(301)
                        self.send_header('Content-type', 'text/html')
                        self.send_header('Location', '/bookstores')
                        self.end_headers()

            if self.path.endswith("/bookstores/new"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))

            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                messagecontent = fields.get('newBookstoreName')

                # Create new Bookstore Object
                newBookstore = Bookstore(name=messagecontent[0])
                session.add(newBookstore)
                session.commit()

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/bookstores')
                self.end_headers()

        except:
            pass


def main():
    try:
        server = HTTPServer(('', 8080), webServerHandler)
        print 'Web server running...open localhost:8080/bookstores in your browser '
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()


if __name__ == '__main__':
    main()
    
    #
