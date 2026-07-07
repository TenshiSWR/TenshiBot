import regex
from tools.misc import LintfixModuleError, log_error


def fix_obsolete_HTML_tags(page: str, text: str) -> str:
    text = regex.sub(r"(<font[^>]*?>[^<\n]*?)<font>(?!((?:(?!<\/font>(?![^<\n]*?<\/font>)).)*?)<\/font>)", r"\1</font\2>", text, flags=regex.DOTALL)  # Will pick up two opening tags even though they close twice
    text = regex.sub(r"<(\/)font[^>]*>", r"<\1span>", text, flags=regex.I)
    if regex.search(r"<\/?font[^>]*>", text, flags=regex.I):
        tags = list(set(regex.findall(r"<\/?font[^>]*>", text, flags=regex.DOTALL|regex.I)))
        for font in tags:
            if regex.search(r"(?:\{\{\{|\}\}\})", font):
                raise LintfixModuleError("Template parameter within font tag", "fix_obsolete_HTML_tags")
            if regex.search(r"<font [^>]+>", font, flags=regex.I):
                params = regex.search(r"<font ([^>]+)>", font, flags=regex.I).group(1)
                new_params = params
                if regex.search(r'color="?([^\s"]+)"?', new_params, flags=regex.I):
                    value = regex.search(r'color="?([^\s"]+)"?', new_params, flags=regex.I).group(1)
                    if regex.search(r"[0-9A-Fa-f]{6}", value):
                        new_params = regex.sub(r'color="?([^\s"]+)"?', r"color: #{};".format(regex.search(r"#?([0-9A-Fa-f]{3,6})", value).group(1)), new_params, flags=regex.I)
                    else:
                        new_params = regex.sub(r'color="?([^\s"]+)"?', r"color: \1;", new_params, flags=regex.I)
                if regex.search(r'size="?([+\-\d]\d*)(?:px)?"?', new_params, flags=regex.I):
                    size = regex.search(r'size= *"? *([+\-\d]\d*)(?:px)?"?', new_params, flags=regex.I).group(1)
                    number = int(regex.search(r"\d+", size).group())
                    if "+" in size[0] or "-" in size[0]:
                        if "+" in size[0]:
                            number = number+3
                        elif "-" in size[0]:
                            number = 3-number
                    if number > 7:
                        number = 7
                    elif number < 1:
                        number = 1
                    new_size = ["x-small", "small", "medium", "large", "x-large", "xx-large", "xxx-large"][number-1]
                    new_params = regex.sub(r'size="?(.\d*)(?:px)?"?', r"font-size: {};".format(new_size), new_params, flags=regex.I)
                elif regex.search(r'size="?[^\s"]+"?', new_params, flags=regex.I):
                    new_params = regex.sub(r'size="?([^\s"]+)"?', r"font-size: \1", new_params, flags=regex.I)
                new_params = regex.sub(r'face="([A-z ,.-]+)"', r"font-family: \1;", new_params, flags=regex.I)
                new_params = regex.sub(r'style="(.+)"', r"\1", new_params, flags=regex.I)
                text = regex.sub(r'<font {}>'.format(regex.escape(params)), r'<span style="{}">'.format(new_params), text, flags=regex.I)
    text = regex.sub(r"(?<!(?:<(nowiki|syntaxhighlight)>(?!(?:(?:(?!(?:<\1>)).)*?)<\/\1>)|<\1>(?:(?:(?!(?:<\/?\1>|<\/?strike>)).)*?)<\/?strike>(?:(?:(?!(?:<\/?\1>)).)*?)<\/nowiki>))(<\/?)(?:[Ss]trike)>(?!(?!.*?<nowiki>).*?<\/nowiki>)", r"\2s>", text, flags=regex.I)
    while True:
        if text != regex.sub(r"<center>((?:(?!(?:{\||\|}(?!\})|(?<!<center>)<\/center>|<\/center>(?=<\/center>)|<\/?gallery>|<center>[^<]*?(?!<\/center>[^<]*?<\/center>))).)*?)<\/center>", r'<div style="text-align: center;">\1</div>', text, flags=regex.DOTALL|regex.I):
            text = regex.sub(r"<center>((?:(?!(?:{\||\|}(?!\})|(?<!<center>)<\/center>|<\/center>(?=<\/center>)|<\/?gallery>|<center>[^<]*?(?!<\/center>[^<]*?<\/center>))).)*?)<\/center>", r'<div style="text-align: center;">\1</div>', text, flags=regex.DOTALL|regex.I)
        else:
            break
    return text
