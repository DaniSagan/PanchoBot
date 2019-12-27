from enum import Enum
from typing import List


class MessageStyle(Enum):
    NONE = 0
    MARKDOWN = 1
    HTML = 2


class TextBase(object):
    def __init__(self, text: str):
        self.text = text

    def format(self, style: MessageStyle):
        raise NotImplementedError()


class NormalText(TextBase):
    def __init__(self, text: str):
        super().__init__(text)

    def format(self, style: MessageStyle):
        return self.text


class BoldText(TextBase):
    def __init__(self, text: str):
        super().__init__(text)

    def format(self, style: MessageStyle):
        if style == MessageStyle.MARKDOWN:
            return '*{t}*'.format(t=self.text)
        elif style == MessageStyle.HTML:
            return '<b>{t}</b>'.format(t=self.text)
        else:
            return self.text


class ItalicText(TextBase):
    def __init__(self, text: str):
        super().__init__(text)

    def format(self, style: MessageStyle):
        if style == MessageStyle.MARKDOWN:
            return '_{t}_'.format(t=self.text)
        elif style == MessageStyle.HTML:
            return '<i>{t}</i>'.format(t=self.text)
        else:
            return self.text


class InlineCode(TextBase):
    def __init__(self, text: str):
        super().__init__(text)

    def format(self, style: MessageStyle):
        if style == MessageStyle.MARKDOWN:
            return '`{t}`'.format(t=self.text)
        elif style == MessageStyle.HTML:
            return '<code>{t}</code>'.format(t=self.text)
        else:
            return self.text


class TextFormatter(object):
    def __init__(self):
        self.items = []  # type: List[TextBase]

    @staticmethod
    def instance() -> 'TextFormatter':
        return TextFormatter()

    def normal(self, text) -> 'TextFormatter':
        self.items.append(NormalText(text))
        return self

    def bold(self, text) -> 'TextFormatter':
        self.items.append(BoldText(text))
        return self

    def italic(self, text) -> 'TextFormatter':
        self.items.append(ItalicText(text))
        return self

    def inline_code(self, text) -> 'TextFormatter':
        self.items.append(InlineCode(text))
        return self

    def format(self, style: MessageStyle) -> str:
        res = ''
        for item in self.items:
            res += item.format(style)
        return res
