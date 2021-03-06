import operator, os, shutil, sys, time, argparse

from common.argparse_util import *
import common.sbd_config as sbd
from preprocessing.sliding_window import SlidingWindow
from preprocessing.tokens import Punctuation
from preprocessing.word2vec_file import Word2VecFile
from preprocessing.glove_file import GloveFile
from parsing.get_parser import *
from level_db_creator import LevelDBCreator


GOOGLE_VECTOR_FILE = "/home/fb10dl01/workspace/ms-2015-t3/GoogleNews-vectors-negative300.bin"
SMALL_VECTOR_FILE = "/home/ms2015t3/vectors.bin"
GLOVE_VECTOR_FILE = "/home/ms2015t3/glove.6B.50d.txt"


class TrainingInstanceGenerator(object):
    """reads the original data, process them and writes them to a level-db"""

    def __init__(self, word2vec):
        self.CLASS_DISTRIBUTION_NORMALIZATION = sbd.config.getboolean('data', 'normalize_class_distribution')
        self.CLASS_DISTRIBUTION_VARIATION = 0.05
        self.USE_QUESTION_MARK = sbd.config.getboolean('features', 'use_question_mark')

        self.word2vec = word2vec
        self.test_talks = set()

    def generate(self, parsers, database, is_test):
        level_db = LevelDBCreator(database)
        window_slider = SlidingWindow()
        # count how often each type (COMMA, PERIOD etc.) is in the instances
        class_distribution = dict()

        nr_instances = 0
        nr_instances_used = 0
        label_nr = len(Punctuation)
        if not self.USE_QUESTION_MARK:
            label_nr -= 1
        perfect_distribution = 1.0 / label_nr

        if is_test:
            plain_text_instances_file = open(database + "/../test_instances.txt", "w")
        else:
            plain_text_instances_file = open(database + "/../train_instances.txt", "w")

        for i, text_parser in enumerate(parsers):
            texts = text_parser.parse()

            prev_progress = 0
            print("")
            print("Processing file %s ..." % text_parser.get_file_name())

            foo = open("lineparsing", "w")
            for text in texts:
                progress = int(text_parser.progress() * 100)
                if progress > prev_progress:
                    sys.stdout.write(str(progress) + "% ")
                    sys.stdout.flush()
                    prev_progress = progress

                for sentence in text.sentences:
                    tokens = sentence.get_tokens()
                    # get the word vectors for all tokens in the sentence
                    for i in range(len(tokens)):
                        token = tokens[i]
                        if not token.is_punctuation():
                            if i == len(tokens) - 1:
                                punctuation_string = "PERIOD"
                            else:
                                next_token = tokens[i + 1]
                                if next_token.is_punctuation():
                                    punctuation_string = str(next_token.punctuation_type)
                                    punctuation_string = punctuation_string[12:]
                                else:
                                    punctuation_string = "O"
                            foo.write(token.word.lower() + "\t" + punctuation_string + "\n")
                            token.word_vec = self.word2vec.get_vector(token.word.lower())

                # get the training instances
                training_instances = window_slider.list_windows(text)

                # write training instances to level db
                for training_instance in training_instances:
                    nr_instances += 1
                    class_variation = (class_distribution.get(training_instance.label, 0) / float(max(nr_instances_used, 1))) - perfect_distribution

                    if is_test or (not self.CLASS_DISTRIBUTION_NORMALIZATION) or (class_variation <= self.CLASS_DISTRIBUTION_VARIATION):
                        # write instance to file
                        s = unicode(training_instance) + "\n"
                        s += "\n"
                        plain_text_instances_file.write(s.encode('utf8'))

                        # adapt class distribution
                        nr_instances_used += 1
                        class_distribution[training_instance.label] = class_distribution.get(training_instance.label, 0) + 1

                        # write to level db
                        level_db.write_training_instance(training_instance)
            foo.close()

        plain_text_instances_file.close()
        print("")

        print("Originally " + str(nr_instances) + " instances.")
        print("Created " + str(nr_instances_used) + " instances." )
        print("Class distribution:")
        print(class_distribution)

    def get_not_covered_words(self):
        return self.word2vec.not_covered_words


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='create test and train datasets as a lmdb.')
    parser.add_argument('config_file', help="path to config file")
    args = parser.parse_args()

    # initialize config
    sbd.SbdConfig(args.config_file)

    # create proper name for the database
    SENTENCE_HOME = os.environ['SENTENCE_HOME']
    data_folder = "/mnt/naruto/sentence/data/"
    LEVEL_DB_DIR = "leveldbs"

    database = SENTENCE_HOME + "/" + LEVEL_DB_DIR + "/" + sbd.SbdConfig.get_db_name_from_config(sbd.config)

    # check if database already exists
    if os.path.isdir(database):
        print("Deleting " + database + ". y/N?")
        sys.stdout.flush()
        s = raw_input()
        if s != "Y" and s != "y":
            print("Not deleting. Exiting ..")
            sys.exit(3)
        shutil.rmtree(database)

    # create database folder and copy config file
    os.mkdir(database)
    shutil.copy(args.config_file, database)

    # get word vector
    word2vec = None
    word_vector_file = sbd.config.get('word_vector', 'vector_file')
    if word_vector_file == "google":
        word2vec = Word2VecFile(GOOGLE_VECTOR_FILE)
    elif word_vector_file == "glove":
        word2vec = GloveFile(GLOVE_VECTOR_FILE)
    elif word_vector_file == "small":
        word2vec = Word2VecFile(SMALL_VECTOR_FILE)

    # get training and test data
    training_data = sbd.config.get('data', 'train_files').split(",")
    test_data = sbd.config.get('data', 'test_files').split(",")

    # get training parsers
    training_parsers = []
    for f in training_data:
        parser = get_parser(data_folder + f)
        if parser is None:
            print("WARNING: Could not find training parser for file %s!" % f)
        else:
            training_parsers.append(parser)

    # get test parsers
    test_parsers = []
    for f in test_data:
        parser = get_parser(data_folder + f)
        if parser is None:
            print("WARNING: Could not find test parser for file %s!" % f)
        else:
            test_parsers.append(parser)

    # generate data
    generator = TrainingInstanceGenerator(word2vec)
    print("Generating test data .. ")
    start = time.time()
    generator.generate(test_parsers, database + "/test", is_test = True)
    duration = int(time.time() - start) / 60
    print("Done in " + str(duration) + " min.")
    if sbd.config.get('word_vector', 'vector_file') == "small":
        print("Stopping after test instance creation")
        sys.exit(0)
    print("Generating training data .. ")
    start = time.time()
    generator.generate(training_parsers, database + "/train", is_test = False)
    duration = int(time.time() - start) / 60
    print("Done in " + str(duration) + " min.")
    print("")
    uncovered = generator.get_not_covered_words()
    print sorted(uncovered.items(), key = operator.itemgetter(1), reverse = True)[:20]
    print("Nr covered tokens: " + str(generator.word2vec.nr_covered_words))
    print("Nr uncovered tokens: " + str(generator.word2vec.nr_uncovered_words))
