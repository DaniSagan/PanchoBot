from html.parser import HTMLParser


class WebParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.seen = {}

    def handle_starttag(self, tag, attributes):
        if tag != 'div': return
        for name, value in attributes:
            if name == 'id' and value == 'remository':
                pass
        return

    def handle_data(self, data):
        print(data)