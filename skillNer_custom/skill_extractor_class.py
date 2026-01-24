# native packs
#
# installed packs
from spacy import displacy

# my packs
from skillNer_custom.text_class import Text
from skillNer_custom.matcher_class import Matchers, SkillsGetter
from skillNer_custom.utils import Utils
from skillNer_custom.general_params import SKILL_TO_COLOR

from skillNer_custom.visualizer.html_elements import DOM, render_phrase
from skillNer_custom.visualizer.phrase_class import Phrase
from skillNer_custom.fuzzy_matcher import FuzzyPhraseMatcher


class SkillExtractor:
    """
    Main class to annotate skills / job titles in a given text.

    PIPELINE OVERVIEW
    -----------------
    1. Full match (exact phrase)
    2. Abbreviation match
    3. Fuzzy phrase match (typo-tolerant, phrase-level)
    4. Full uni-gram match
    5. Low surface match
    6. Token-level match
    7. Conflict resolution via n-gram scoring

    IMPORTANT DESIGN NOTE
    ---------------------
    - Fuzzy matcher is executed EARLY and directly mutates text_obj
      by marking matched tokens as `is_matchable = False`
    - This prevents low-level matchers (lowSurf / token)
      from stealing parts of a valid fuzzy phrase
    """

    def __init__(
        self,
        nlp,
        skills_db,
        phraseMatcher,
        tranlsator_func=False,
        fuzzy_func=False
    ):
        """
        Constructor of the class.

        Parameters
        ----------
        nlp : spacy.Language
            NLP object loaded from spacy.
        skills_db : dict
            Skill database used as a lookup table.
        phraseMatcher : spacy.matcher.PhraseMatcher
            PhraseMatcher instance.
        tranlsator_func : Callable | False
            Optional translation function.
        fuzzy_func : bool
            Enable fuzzy phrase matcher.
        """

        # params
        self.tranlsator_func = tranlsator_func
        self.fuzzy_func = fuzzy_func
        self.nlp = nlp
        self.skills_db = skills_db
        self.phraseMatcher = phraseMatcher

        # --------------------------------------------------
        # Load ALL deterministic matchers
        # --------------------------------------------------
        self.matchers = Matchers(
            self.nlp,
            self.skills_db,
            self.phraseMatcher,
        ).load_matchers()

        # --------------------------------------------------
        # Load fuzzy phrase matcher
        # --------------------------------------------------
        # Fuzzy matcher works on PHRASE level
        # and handles typo / noisy spans
        self.fuzzy_matcher = FuzzyPhraseMatcher(
            self.skills_db,
        )

        # init skill getters (wrappers around spacy matchers)
        self.skill_getters = SkillsGetter(self.nlp)

        # init utils (n-gram conflict resolver, scoring, etc.)
        self.utils = Utils(self.nlp, self.skills_db)
        return

    def annotate(
        self,
        text: str,
        tresh: float = 0.5
    ) -> dict:
        """
        Annotate skills / job titles in input text.

        FUZZY INTEGRATION STRATEGY
        -------------------------
        - Fuzzy matcher runs AFTER full & abv match
        - BEFORE low-level matchers
        - Fuzzy matcher marks consumed tokens as unmatchable
        - Its results are returned separately (not mixed into ngram_scored)

        This avoids:
        - developer eating python developer
        - lowSurf overriding fuzzy phrase
        """

        # optional translation
        if self.tranlsator_func:
            text = self.tranlsator_func(text)

        # create text object (tokenized + is_matchable flags)
        text_obj = Text(text, self.nlp)

        # --------------------------------------------------
        # 1. FULL MATCH
        # --------------------------------------------------
        skills_full, text_obj = self.skill_getters.get_full_match_skills(
            text_obj, self.matchers['full_matcher'])

        # --------------------------------------------------
        # 2. ABBREVIATION MATCH
        # --------------------------------------------------
        skills_abv, text_obj = self.skill_getters.get_abv_match_skills(
            text_obj, self.matchers['abv_matcher'])

        # --------------------------------------------------
        # 3. FUZZY PHRASE MATCH (TYPO-TOLERANT)
        # --------------------------------------------------
        # This step MUTATES text_obj:
        # matched tokens are marked as is_matchable = False
        if self.fuzzy_func:
            # fuzzy matcher WILL mark matched tokens as is_matchable = False
            fuzzy_matches = self.fuzzy_matcher.match(text_obj)
        else:
            fuzzy_matches = []
        # --------------------------------------------------
        # 4. FULL UNI-GRAM MATCH
        # --------------------------------------------------
        skills_uni_full, text_obj = self.skill_getters.get_full_uni_match_skills(
            text_obj, self.matchers['full_uni_matcher'])

        # --------------------------------------------------
        # 5. LOW SURFACE MATCH
        # --------------------------------------------------
        skills_low_form, text_obj = self.skill_getters.get_low_match_skills(
            text_obj, self.matchers['low_form_matcher'])

        # --------------------------------------------------
        # 6. TOKEN MATCH
        # --------------------------------------------------
        skills_on_token = self.skill_getters.get_token_match_skills(
            text_obj, self.matchers['token_matcher'])

        # deterministic matches
        full_sk = skills_full + skills_abv

        # candidates for n-gram conflict resolution
        to_process = skills_on_token + skills_low_form + skills_uni_full

        # --------------------------------------------------
        # 7. N-GRAM SCORING & CONFLICT RESOLUTION
        # --------------------------------------------------
        process_n_gram = self.utils.process_n_gram(to_process, text_obj)

        return {
            'text': text_obj.transformed_text,
            'results': {
                'full_matches': full_sk,
                'ngram_scored': [
                    match for match in process_n_gram
                    if match['score'] >= tresh
                ],
                'fuzzy_matches': [
                    match for match in fuzzy_matches
                    if match['score'] >= tresh
                ]
            }
        }


    def display(
        self,
        results: dict
    ):
        """To display the annotated skills. 
        This method uses built-in classes of spacy to render annotated text, namely `displacy`.

        Parameters
        ----------
        results : dict
            results is the dictionnary resulting from applying `.annotate()` to a text.

        Results
        -------
        None 
            render the text with annotated skills.
        """

        # explode result object
        text = results["text"]
        skill_extractor_results = results['results']

        # words and their positions
        words_position = Text.words_start_end_position(text)

        # get matches
        matches = []
        for match_type in skill_extractor_results.keys():
            for match in skill_extractor_results[match_type]:
                matches.append(match)

        # displacy render params
        entities = []
        colors = {}
        colors_id = []

        # fill params
        for match in matches:
            # skill id
            skill_id = match["skill_id"]

            # index of words in skill
            index_start_word, index_end_word = match['doc_node_id'][0], match['doc_node_id'][-1]

            # build/append entity
            entity = {
                "start": words_position[index_start_word].start,
                "end": words_position[index_end_word].end,
                "label": self.skills_db[skill_id]['skill_name']
            }
            entities.append(entity)

            # highlight matched skills
            colors[entity['label']
                   ] = SKILL_TO_COLOR[self.skills_db[skill_id]['skill_type']]
            colors_id.append(entity['label'])

        # prepare params
        entities.sort(key=lambda x: x['start'], reverse=False)
        options = {"ents": colors_id, "colors": colors}
        ex = {
            "text": text,
            "ents": entities,
            "title": None
        }

        # render
        html = displacy.render(ex, style="ent", manual=True, options=options)

    def describe(
        self,
        annotations: dict
    ):
        """To display more details about the annotated skills.
        This method uses HTML, CSS, JavaScript combined with IPython to render the annotated skills.

        Parameters
        ----------
        annotations : dict
            annotations is the dictionnary resulting from applying `.annotate()` to a text.

        Returns
        -------
        [type]
            render text with annotated skills.
        """

        # build phrases to display from annotations
        arr_phrases = Phrase.split_text_to_phare(
            annotations,
            self.skills_db
        )

        # create DOM
        document = DOM(children=[
            render_phrase(phrase)
            for phrase in arr_phrases
        ])

        # render
        return document
