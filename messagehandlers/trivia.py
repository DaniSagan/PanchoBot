import html
import random
from typing import Dict
from typing import List

import time

import utils
from bot import MessageHandlerBase, BotBase, InlineKeyboardMarkup, MessageStyle
from data import Message, ChatState, CallbackQuery

CATEGORIES = {'any': 'Any',
              '9': 'General Knowledge',
              '10': 'Entertainment: Books',
              '11': 'Entertainment: Film',
              '12': 'Entertainment: Music',
              '13': 'Entertainment: Musicals & Theatres',
              '14': 'Entertainment: Television',
              '15': 'Entertainment: Video Games',
              '16': 'Entertainment: Board Games',
              '17': 'Science & Nature',
              '18': 'Science: Computers',
              '19': 'Science: Mathematics',
              '20': 'Mythology',
              '21': 'Sports',
              '22': 'Geography',
              '23': 'History',
              '24': 'Politics',
              '25': 'Art',
              '26': 'Celebrities',
              '27': 'Animals',
              '28': 'Vehicles',
              '29': 'Entertainment: Comics',
              '30': 'Science: Gadgets',
              '31': 'Entertainment: Japanese Anime & Manga',
              '32': 'Entertainment: Cartoon & Animations'}


class TriviaQuestion(object):
    def __init__(self):
        self.category = ''  # type: str
        self.type = ''  # type: str
        self.difficulty = ''  # type: str
        self.question = ''  # type: str
        self.correct_answer = ''  # type: str
        self.incorrect_answers = []  # type: [str

    @staticmethod
    def from_json(json_object: Dict) -> 'TriviaQuestion':
        res = TriviaQuestion()
        res.category = json_object['category']
        res.type = json_object['type']
        res.difficulty = json_object['difficulty']
        res.question = html.unescape(json_object['question'])
        res.correct_answer = json_object['correct_answer']
        res.incorrect_answers = json_object['incorrect_answers']
        return res


class AnswerArrangement(object):
    def __init__(self):
        self.answers = []  # type: List[str]
        self.correct_answer_index = 0  # type: int

    @staticmethod
    def generate_random_from_question(question: TriviaQuestion):
        res = AnswerArrangement()
        r = [a for a in question.incorrect_answers]
        random.shuffle(r)  # type: List[str]
        i = random.randint(0, len(r))
        r.insert(i, question.correct_answer)
        res.answers = r
        res.correct_answer_index = i
        return res


class Trivia(MessageHandlerBase):
    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None):
        if chat_state is not None:
            self.process_answer(message, bot, chat_state)
        else:
            self.process_new_question(message, bot)

    def process_callback_query(self, callback_query: CallbackQuery, bot: BotBase, chat_state: ChatState = None):
        if chat_state is None:
            pass
        else:
            try:
                given_answer_idx = int(callback_query.data) - 1  # type: int
                answers = chat_state.data['answers']  # type: AnswerArrangement
                if given_answer_idx == answers.correct_answer_index:
                    bot.send_message(callback_query.message.chat, 'Correct!!', MessageStyle.NONE)
                else:
                    bot.send_message(callback_query.message.chat,
                                     'WRONG. The answer was:\n{k}. {a}'.format(k=answers.correct_answer_index + 1,
                                                                               a=answers.answers[
                                                                                   answers.correct_answer_index]), MessageStyle.NONE)
                bot.answer_callback_query(callback_query.id_callback_query)
                callback_query.message.chat.remove_chat_state()
            except Exception as ex:
                raise RuntimeError('Could not process answer: ' + str(ex))

    def process_new_question(self, message: Message, bot: BotBase):
        words = message.text.split(' ')
        if words[0].lower() == 'trivia':
            # json_obj = utils.get_url_json('https://opentdb.com/api.php', {'amount': '1'})
            json_obj = utils.get_url_json('https://opentdb.com/api.php?amount=1')
            question = TriviaQuestion.from_json(json_obj['results'][0])  # type: TriviaQuestion
            answers = AnswerArrangement.generate_random_from_question(question)  # type: AnswerArrangement
            keyboard = InlineKeyboardMarkup.from_str_list([str(k+1) for k in range(len(answers.answers))])  # type: InlineKeyboardMarkup
            bot.send_message_with_inline_keyboard(message.chat,
                                                  self.get_question_str(question, answers),
                                                  MessageStyle.NONE,
                                                  keyboard)

            state = ChatState()
            state.current_handler_name = self.handler_name
            state.chat_id = message.chat.id_chat
            state.last_time = time.time()
            state.data['question'] = question
            state.data['answers'] = answers
            message.chat.save_chat_state(state)

    def process_answer(self, message: Message, bot: BotBase, chat_state: ChatState):
        try:
            given_answer_idx = int(message.text) - 1  # type: int
            answers = chat_state.data['answers']  # type: AnswerArrangement
            if given_answer_idx == answers.correct_answer_index:
                bot.send_message(message.chat, 'Correct!!', MessageStyle.NONE)
            else:
                bot.send_message(message.chat,
                                 'WRONG. The answer was:\n{k}. {a}'.format(k=answers.correct_answer_index+1,
                                                                           a=answers.answers[
                                                                              answers.correct_answer_index]),
                                 MessageStyle.NONE)
            message.chat.remove_chat_state()
        except Exception as ex:
            raise RuntimeError('Could not process answer: ' + str(ex))

    def get_question_str(self, question: TriviaQuestion, answers: AnswerArrangement) -> str:
        answer_str = '\n'.join(['{k}. {q}'.format(k=i+1, q=q) for i, q in enumerate(answers.answers)])
        return '{q}\n\n{a}'.format(q=question.question, a=answer_str)
