from pymei import MeiDocument, MeiElement, documentToText


class MeiOutput(object):

    # define the form of a neume.
    # form: [ num, interval_dir... ]
    # e.g., clivis: [2, 'd']
    # torculus: [3, 'u', 'd']
    NEUME_NOTES = {
        'punctum': [],
        'virga': [],
        'cephalicus': ['d'],
        'clivis': ['d'],
        'epiphonus': ['u'],
        'podatus': ['u'],
        'porrectus': ['d', 'u'],
        'salicus': ['u', 'u'],
        'scandicus': ['u', 'u'],
        'torculus': ['u', 'd'],
        'ancus': ['d', 'd'],  # See note 1 below
    }

    NEUME_NAMES = [
        'punctum',
        'virga',
        'cephalicus',
        'clivis',
        'epiphonus',
        'podatus',
        'porrectus',
        'salicus',
        'scandicus',
        'torculus',
        'ancus',
    ]

    # given an alternate form, how many notes does it add to the neume?
    ADD_NOTES = {
        'flexus': ['d'],  # scandicus.flexus, porrectus.flexus
        'resupinus': ['u'],  # torculus.resupinus
    }

    SCALE = ['a', 'b', 'c', 'd', 'e', 'f', 'g']

    def __init__(self, incoming_data, version, **kwargs):
        self.incoming_data = incoming_data
        self.version = version
        self.currentGlyph = 0

    def run(self):

        print(self.incoming_data[0])

        if self.version == 'N':
            return self.conversion()
        else:
            print('not valid MEI version')

    def conversion(self):
        print('begin conversion')

        doc = self.createDoc()

        return documentToText(doc)

    def createDoc(self):
        # initialize basic universal attributes of any MEI document
        doc = MeiDocument()

        self._generate_mei(doc)
        # self._generate_meiCorpus(doc)     # unnecesary

        return doc

    def _findRelativeNote(self, startOctave, startNote, contour, interval):

        startOctave = int(startOctave)
        interval = int(interval) - 1  # because intervals are 1 note off

        if contour == 'u':      # upwards
            newOctave = startOctave + int((self.SCALE.index(startNote) + interval) / len(self.SCALE))
            newNote = self.SCALE[(self.SCALE.index(startNote) + interval) % len(self.SCALE)]

        elif contour == 'd':    # downwards
            newOctave = startOctave - \
                int((len(self.SCALE) - self.SCALE.index(startNote) - 1 + interval) / len(self.SCALE))
            newNote = self.SCALE[(self.SCALE.index(startNote) - interval) % len(self.SCALE)]

        return [str(newOctave), newNote]

    def _generate_mei(self, parent):
        el = MeiElement("mei")
        parent.root = el

        el.addAttribute("meiversion", self.version)

        self._generate_meiHead(el)
        self._generate_music(el)

    def _generate_meiHead(self, parent):
        el = MeiElement("meiHead")
        parent.addChild(el)

    def _generate_music(self, parent):
        el = MeiElement("music")
        parent.addChild(el)

        # self._generate_front(el)          # unnecesary
        self._generate_body(el)
        # self._generate_back(el)           # unnecesary

    def _generate_body(self, parent):
        el = MeiElement("body")
        parent.addChild(el)

        self._generate_mdiv(el)

    def _generate_mdiv(self, parent):
        # LATER CHECK FOR SUBDIVS, multi movement pieces, etc.
        el = MeiElement("mdiv")
        parent.addChild(el)

        self._generate_score(el)

    def _generate_score(self, parent):
        el = MeiElement("score")
        parent.addChild(el)

        self._generate_scoreDef(el)
        self._generate_section(el)

    def _generate_scoreDef(self, parent):
        el = MeiElement("scoreDef")
        parent.addChild(el)

        self._generate_staffGrp(el)

    def _generate_section(self, parent):
        el = MeiElement("section")
        parent.addChild(el)

        # find number of staves
        numStaves = int(self.incoming_data[len(
            self.incoming_data) - 1]['pitch']['staff'])
        for i in list(range(numStaves)):
            self._generate_staff(el, i)     # generate multiple staves

    def _generate_staffGrp(self, parent):
        el = MeiElement("staffGrp")
        parent.addChild(el)

        self._generate_staffDef(el)

    def _generate_staffDef(self, parent):
        el = MeiElement("staffDef")
        parent.addChild(el)

    def _generate_staff(self, parent, i):
        el = MeiElement("staff")
        parent.addChild(el)

        el.addAttribute('n', str(i + 1))

        self._generate_layer(el)
        # neume only get 1 layer per staff, worth verifying later

    def _generate_layer(self, parent):
        el = MeiElement("layer")
        parent.addChild(el)

        # for each glyph in this staff, make a syllable
        localGlyphs = list(filter(lambda g: g['pitch']['staff'] ==
                                  el.getParent().getAttribute('n').value, self.incoming_data))

        for g in localGlyphs:
            glyphName = g['glyph']['name'].split('.')

            if glyphName[0] == 'clef':
                self._generate_clef(el, g)
            elif glyphName[0] == 'custos':
                self._generate_custos(el, g)
            else:
                self._generate_syllable(el, g)

    def _generate_clef(self, parent, glyph):
        el = MeiElement("clef")
        parent.addChild(el)

        # self._generate_(el)

    def _generate_custos(self, parent, glyph):
        el = MeiElement("custos")
        parent.addChild(el)

        # self._generate_(el)

    def _generate_syllable(self, parent, glyph):
        el = MeiElement("syllable")
        parent.addChild(el)

        self._generate_syl(el, glyph)
        self._generate_neume(el, glyph)     # this may need to change

    def _generate_syl(self, parent, glyph):
        el = MeiElement("syl")
        parent.addChild(el)

        # self._generate_(el)

    def _generate_neume(self, parent, glyph):
        el = MeiElement("neume")
        parent.addChild(el)

        glyphName = glyph['glyph']['name'].split('.')
        glyphOctave = glyph['pitch']['octave']
        glyphNote = glyph['pitch']['note']
        glyphVisuals = {
            'diagonalright': False,
            'con': False,
            'intm': False
        }

        if glyphName[1] == 'punctum':
            self._generate_nc(el, glyphOctave, glyphNote, **glyphVisuals)

        elif glyphName[1] == 'virga':
            self._generate_nc(el, glyphOctave, glyphNote, **glyphVisuals)

        # elif glyphName[1] == 'cephalicus':

        elif glyphName[1] == 'clivis':
            self._generate_nc(el, glyphOctave, glyphNote, **glyphVisuals)
            newPitch = self._findRelativeNote(glyphOctave, glyphNote, 'd', glyphName[2])
            self._generate_nc(el, newPitch[0], newPitch[1], **glyphVisuals)

        # elif glyphName[1] == 'epiphonus':

        elif glyphName[1] == 'podatus':
            self._generate_nc(el, glyphOctave, glyphNote, **glyphVisuals)
            newPitch = self._findRelativeNote(glyphOctave, glyphNote, 'u', glyphName[2])
            self._generate_nc(el, newPitch[0], newPitch[1], **glyphVisuals)

        elif glyphName[1] == 'porrectus':
            self._generate_nc(el, glyphOctave, glyphNote, **glyphVisuals)
            newPitch = self._findRelativeNote(glyphOctave, glyphNote, 'd', glyphName[2])
            self._generate_nc(el, newPitch[0], newPitch[1], **glyphVisuals)
            newPitch = self._findRelativeNote(newPitch[0], newPitch[1], 'u', glyphName[3])
            self._generate_nc(el, newPitch[0], newPitch[1], **glyphVisuals)

        # elif glyphName[1] == 'salicus':

        elif glyphName[1] == 'scandicus':
            self._generate_nc(el, glyphOctave, glyphNote, **glyphVisuals)
            newPitch = self._findRelativeNote(glyphOctave, glyphNote, 'u', glyphName[2])
            self._generate_nc(el, newPitch[0], newPitch[1], **glyphVisuals)
            newPitch = self._findRelativeNote(newPitch[0], newPitch[1], 'u', glyphName[3])
            self._generate_nc(el, newPitch[0], newPitch[1], **glyphVisuals)

        elif glyphName[1] == 'torculus':
            self._generate_nc(el, glyphOctave, glyphNote, **glyphVisuals)
            newPitch = self._findRelativeNote(glyphOctave, glyphNote, 'u', glyphName[2])
            self._generate_nc(el, newPitch[0], newPitch[1], **glyphVisuals)
            newPitch = self._findRelativeNote(newPitch[0], newPitch[1], 'd', glyphName[3])
            self._generate_nc(el, newPitch[0], newPitch[1], **glyphVisuals)

        # elif glyphName[1] == 'ancus':

    def _generate_nc(self, parent, octave, pname, **kwargs):
        el = MeiElement("nc")
        parent.addChild(el)

        if kwargs['diagonalright']:
            el.addAttribute("diagonalright", kwargs['diagonalright'])
        if kwargs['con']:
            el.addAttribute("con", kwargs['con'])
        if kwargs['intm']:
            el.addAttribute("intm", kwargs['intm'])

        el.addAttribute("oct", octave)
        el.addAttribute("pname", pname)

        # self._generate_(el)

    def _generate_(self, parent):
        el = MeiElement("")
        parent.addChild(el)

        # self._generate_(el)

    def _generate_(self, parent):
        el = MeiElement("")
        parent.addChild(el)

        # self._generate_(el)

    def _generate_(self, parent):
        el = MeiElement("")
        parent.addChild(el)

        # self._generate_(el)

    def _generate_(self, parent):
        el = MeiElement("")
        parent.addChild(el)

        # self._generate_(el)
