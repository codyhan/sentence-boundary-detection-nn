import sys
import os
import talk_parsing
import sliding_window
import word2vec_file
import create_level_db


WORD_VECTOR_FILE = "/home/fb10dl01/workspace/ms-2015-t3/GoogleNews-vectors-negative300.bin"
LEVEL_DB_DIR = "/home/ms2015t3/sentence-boundary-detection-nn/leveldbs/"

class TrainingSampleGenerator():

    def generate(self, training_data, database):
        for training_paths in training_data:
            talk_parser = talk_parsing.TalkParser(training_paths[0], training_paths[1])
            talks = talk_parser.list_talks()

            window_slider = sliding_window.SlidingWindow()
            word2Vec = word2vec_file.Word2VecFile(WORD_VECTOR_FILE)
            level_db = create_level_db.CreateLevelDB(LEVEL_DB_DIR + database)

            for talk in talks:
                for sentence in talk.sentences:
                    # get the word vectors for all token in the sentence
                    for token in sentence.gold_text:
                        token.word_vec = word2Vec.get_vector(token)

                    # get the training instances
                    training_instance = window_slider.list_windows(sentence)

                    # write training instances to level db
                    level_db.write_training_instance(training_instance)

                    # print (training_instance)


if __name__=='__main__':

    argc = len(sys.argv)
    if argc != 2:
        print "Usage: " + sys.argv[0] + " [data_folder]"
        sys.exit(1)

    data_folder = sys.argv[1]
    sentence_home = os.environ['SENTENCE_HOME']

    print "Deleting " + sentence_home + "/leveldbs/" + data_folder + ". Y/n?"
    s = raw_input()
    if s != "Y":
        print "Not deleting. Exiting .."
        sys.exit(2)

    database = sentence_home + "/leveldbs/" + data_folder
    if os.path.isdir(database):
        import shutil
        shutil.rmtree(database)

    training_data = [
        ("/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/dev2010-w/IWSLT15.TED.dev2010.en-zh.en.xml",
            "/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/dev2010-w/word-level transcript/dev2010.en.talkid<id>_sorted.txt"),
        ("/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/tst2010-w/IWSLT15.TED.tst2010.en-zh.en.xml", None),
        ("/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/tst2012-w/IWSLT12.TED.MT.tst2012.en-fr.en.xml", None),
        ("/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/tst2013-w/IWSLT15.TED.tst2013.en-zh.en.xml", None)
    ]
    test_data = [
        ("/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/tst2013-w/IWSLT12.TED.MT.tst2011.en-fr.en.xml", None)
    ]

    generator = TrainingSampleGenerator()
    generator.generate(training_data, data_folder + "/train")
    generator.generate(test_data, data_folder + "/test")