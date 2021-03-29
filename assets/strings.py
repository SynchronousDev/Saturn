from assets import *
import typing

def clean_codeblock(content) -> str:
    """
    Clean a codeblock of the ``` and the pys.
    """
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:])[:-3]
    else:
        return content


def flatten(l: typing.Union[list, tuple]) -> list:
    """
    Flatten nested lists into normal lists
    """
    _list = []
    l = list(l)
    while l:
        e = l.pop()
        if isinstance(e, list):
            l.extend(e)

        else:
            _list.append(e)

    return list(reversed(_list))