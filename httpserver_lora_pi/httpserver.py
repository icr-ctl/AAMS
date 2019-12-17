from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
import re

classids = []
confs = []
seenall = {}
pktnum = 0
thous = 0

def load_labels(path):
    p = re.compile(r'\s*(\d+)(.+)')
    with open(path, 'r', encoding='utf-8') as f:
       lines = (p.match(line).groups() for line in f.readlines())
       return {int(num): text.strip() for num, text in lines}

labels = load_labels('coco_labels.txt')

class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        global classids
        global confs
        global pktnum
        global thous
        global seenall
        print("packet number: " + str(pktnum))
        """Respond to a GET request."""
        try:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            #self.wfile.write(f.read())
            self.wfile.write(b'<html><head><title>LoRa Transmission</title>')
            self.wfile.write(b'<style>')
            self.wfile.write(b'table,th,td {border: 1px solid black;}')
            self.wfile.write(b'</style>')
            self.wfile.write(b'<meta http-equiv="refresh" content="5" /></head>')
            self.wfile.write(b'<body style="background-color:coral;text-align:center;"><h1 style="margin:15px">Autonomous Animal Monitoring System</h1>')
            self.wfile.write(b'<p style="text-align:center;">A simple HTTP server to keep track of the LoRa tranmission.</p>')
            self.wfile.write(b'<hr>')
            self.wfile.write(b'')
            self.wfile.write(b'<h3>Current packet number: %d</h3>' % (pktnum+thous))
            self.wfile.write(b'')
            self.wfile.write(b'<table align="center" style="width:50%"><tr><th>Class Name</th><th>Instances</th></tr>')
            for k,v in seenall:
                self.wfile.write(b'<tr><td>%b</td><td>%d</td></tr>' % (bytes(k, "utf-8"), v))
            self.wfile.write(b'</table>')
            self.wfile.write(b'<div class="row">')
            highconf = []
            other = []
            for i in range(len(classids)):
                if confs[i] > 40:
                    highconf.append(i)
                else:
                    other.append(i)
            self.wfile.write(b'<div style="float:left;width:50%;"><h2>Seen with high confidence</h2>')
            for i in highconf:
                classname = labels[classids[i]]
                if classname in seenall:
                    seenall[classname] += 1
                else:
                    seenall[classname] = 1
                self.wfile.write(b'<h4>%b: %d</h4>\%' % (bytes(labels[classids[i]], "utf-8"), confs[i]))
            self.wfile.write(b'</div>')
            self.wfile.write(b'<div style="float:left;width:50%"><h2>Seen with low confidence</h2>')
            for i in other:
                self.wfile.write(b'<h4>%b: %d</h4>\%' % (bytes(labels[classids[i]], "utf-8"), confs[i]))
            self.wfile.write(b'</div></div>')
            self.wfile.write(b'</body></html>')

            return
        except IOError:
            self.send_error(404, "File Not Found: %s" % self.path)

    def do_POST(self):
        global classids
        global confs
        global pktnum
        global thous
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print("**********************")
        js = json.loads(post_data)
        classids = js["object"]["Object_IDs"]
        confs = js["object"]["Confidences"]
        pktnum = js["object"]["Packet_Number"]
        thous = js["object"]["Thousands"]
        print("Recieved data!")
        #logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n", str(self.path), str(self.headers), post_data.decode('utf-8'))

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=S, port=8000):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__=='__main__':
    run()
