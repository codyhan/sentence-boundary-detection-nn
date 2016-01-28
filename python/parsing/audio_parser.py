from parsing.get_parser import *
from sbd_classification.classification_input import InputText
from sbd_classification.classification_input import InputAudio
from preprocessing.tokens import WordToken
from preprocessing.nlp_pipeline import NlpPipeline

class AudioParser(object):

    def __init__(self, ctm_file, pitch_file, energy_file):
        self.ctm_file = ctm_file
        self.pitch_file = pitch_file
        self.energy_file = energy_file
        self.talks = None
        self.talk = None

    def parse(self):
        parser = get_parser(self.ctm_file)
        talks = parser.parse()

        self.talks = []
        for i, talk in enumerate(talks):
            talk.build_interval_tree()

            # get pitch feature values
            talk.parse_pitch_feature(self.pitch_file)
            # get energy feature values
            talk.parse_energy_feature(self.energy_file)
            # normalize features
            talk.normalize()

            self.talks.append(talk)

        self.talk = self.talks[0]

    def get_text(self):
        text = ""
        for token in self.talk.get_tokens():
            if not token.is_punctuation():
                text += token.word + " "
        return text

    def get_input_text(self):
        text = ""
        for token in self.talk.get_tokens():
            if not token.is_punctuation():
                text += token.word + " "
        return InputText(str(text))

    def get_input_audio(self):
        tokens = []
        for token in self.talk.get_tokens():
            if not token.is_punctuation():
                tokens.append(token)
        return InputAudio(tokens)
