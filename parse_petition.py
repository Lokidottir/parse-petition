from html.parser import HTMLParser
import os.path, time, datetime, json, sys, textwrap

class ParsePetition(HTMLParser):
    """
        A class for parsing petitions from petition.parliament.uk
    """

    def __init__(self, filepath, last_count = 0, feed = True):
        """
            filepath is the string of the location of the file to
            parse, this is needed to get the time of the creation
            of the file.

            last_count is the number of signatures from the last
            time the petition page was parsed

            feed is a boolean of if the file should be parsed during
            construction, because someone might not want to, options!
        """
        HTMLParser.__init__(self)
        self.is_at_count = False
        self.sig_count = None
        self.filepath = filepath
        self.sig_time = os.path.getctime(filepath)
        self.last_count = last_count
        if feed:
            self.feed(open(filepath).read())

    def handle_starttag(self, tag, attrs):
        if tag == "p" and self.sig_count == None:
            self.is_at_count = ("class", "signature-count-number") in attrs
        return

    def handle_endtag(self, tag):
        if self.is_at_count:
            self.is_at_count = False

    def handle_data(self, _data):
        if self.is_at_count:
            data = _data.replace(",", "")
            self.sig_count = int(data)
            self.is_at_count = False
        else:
            return

    def feed(self, *other):
        HTMLParser.feed(self, other)
        if self.sig_count == None:
            raise ValueError("Could not parse the petition count from file '%s'" % (self.filepath))


    def toJSON(self):
        """
            Returns a JSON representation of the parsed data,
            which is the time (from the file's ctime), the
            number of signatures, and the change in signatures
            (if the previous number of signatures was given
            at construction)

            Format:
            {
                "time": <time formatted as JS's Date.toJSON>,
                "signatures": <number of signatures>,
                "delta_signatures": <change in number of signatures>
            }
        """
        dict_rep = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(self.sig_time)),
            "signatures": self.sig_count,
            "delta_signatures": self.sig_count - self.last_count
        }
        return dict_rep

__parse_petition_helptext__ = """\
parse-petition written by lokidottir, available under the MIT Licence
    usage:
        parse-petition <data file> <files...>
        args:
            data file:
                any json file of any name that contains
                an array of data points to append the data
                points parsed by this program to.
            files...:
                files to parse, data points are appended to
                the data file.
"""

def main(args):
    if len(args) > 1:

        if not os.path.exists(args[1]):
            _datafile = open(args[1], "w+")
            _datafile.write("[]")
            _datafile.close()

        filepaths = args[2:]
        datafile = open(args[1], "r+")
        data = json.loads(datafile.read())
        datafile.seek(0)
        datafile.truncate()
        previous_count = None

        if len(data) > 0:
            previous_count = data[-1]["signatures"]
        else:
            previous_count = 0

        for path in filepaths:
            datapoint = ParsePetition(path, previous_count)
            data.append(datapoint.toJSON())
            previous_count = datapoint["signatures"]

        datafile.write(json.dumps(data))
        datafile.close()
    else:
        print(__parse_petition_helptext__)

if __name__ == '__main__':
    main(sys.argv)
