import common.sbd_config as sbd
import json, caffe, argparse
from sbd_classification.util import *
from sbd_classification.lexical_classification import LexicalClassifier
from flask import Flask, render_template, request
from os import walk, listdir
from preprocessing.word2vec_file import Word2VecFile
from preprocessing.nlp_pipeline import PosTag

app = Flask(__name__)

route_folder = ''
config_file = None
folder = ''
text_folder = ''

DEBUG = True

def get_options(route_folder):
    f = []
    for (dirpath, dirnames, filenames) in walk(route_folder):
        f.extend(dirnames)
        break
    return f

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/classify", methods = ['POST'])
def classify():
    assert request.method == 'POST'
    text_file = request.form['textfile']
    print text_file
    text = ""
    if text_file == 'None':
        text = request.form['text']
    else:
        file_name = "%s/%s" % (text_folder, text_file)
        with open(file_name) as f:
            text = f.read()

    data = classifier.predict_text(text)
    return json.dumps(data)

@app.route("/files", methods = ['GET'])
def getTextFiles():
    assert request.method == 'GET'
    f = []
    for (dirpath, dirnames, filenames) in walk(text_folder):
        for filename in filenames:
            if not filename.endswith(".result"):
                f.append(filename)
    return json.dumps(f)

@app.route("/settings", methods = ['GET'])
def getSettingOptions():
    assert request.method == 'GET'
    f = get_options(route_folder)
    response = {"selected": f[0], "options":f}
    return json.dumps(response)

@app.route("/settings", methods = ['POST'])
def changeSettings():
    global classifier
    assert request.method == 'POST'
    classifier = settings(route_folder + str(request.form['folder']), vector)
    return ('', 200)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run the web demo')
    parser.add_argument('routefolder', help='the main directory containing all possible configurations', default='demo_data/lexical_models/', nargs='?')
    parser.add_argument('textfolder', help='the main directory containing all text files to test', default='demo_text/', nargs='?')
    parser.add_argument('vectorfile', help='the google news word vector', default='models/GoogleNews-vectors-negative300.bin', nargs='?')
    parser.add_argument('-nd','--no-debug', help='do not use debug mode, google vector is read', action='store_false', dest='debug', default=DEBUG)
    args = parser.parse_args()

    route_folder = args.routefolder + "/"
    option_list = get_options(route_folder)
    print option_list
    folder = option_list[0]
    text_folder = args.textfolder

    config_file, caffemodel_file, net_proto = get_filenames(route_folder + folder)

    config_file = sbd.SbdConfig(config_file)

   # net = caffe.Net(args.caffeproto, args.caffemodel, caffe.TEST)
    if not args.debug:
        vector = Word2VecFile(args.vectorfile)
       # classifier = Classifier(net, vector, False)
        classifier = settings(route_folder + folder, vector)
        app.run(debug = True, use_reloader = False)
    else:
        vector = None
        classifier = settings(route_folder + folder, vector)
        app.run(debug = True)
