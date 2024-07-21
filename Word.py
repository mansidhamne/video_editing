class Word:
    def __init__(self, dict, model):
        if model == "vosk":
            self.conf = dict["conf"]
            self.word = dict["word"]
        else:
            self.confidence = dict["confidence"]
            self.word = dict["text"]
        self.end = dict["end"]
        self.start = dict["start"]
        
    def to_word(self):
        return self.word

    def to_string(self):
        return "{:20} from {:.2f} sec to {:.2f} sec, confidence is {:.2f}%".format(
            self.word, self.start, self.end, self.confidence*100)