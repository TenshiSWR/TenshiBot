import regex


def fix_obsolete_HTML_tags(page: str, text: str) -> str:
    text = regex.sub(r"<(\/)font>", r"<\1span>", text)
    if regex.search(r"<\/?font[^>]*>", text):
        tags = list(set(regex.findall(r"<\/?font[^>]*>", text, flags=regex.DOTALL)))
        for font in tags:
            if regex.search(r"<font[^>]+>", font):
                params = regex.search(r"<font ([^>]+)>", font).group(1)
                new_params = params
                if regex.search(r'color="?([^"]+)"?', new_params):
                    value = regex.search(r'color="?([^"]+)"?', new_params).group(1)
                    if regex.search(r"[0-9A-Fa-f]{6}", value):
                        new_params = regex.sub(r'color="?([^"]+)"?', r"color: #{};".format(regex.search(r"#?([0-9A-Fa-f]{6})", value).group(1)), new_params)
                    else:
                        new_params = regex.sub(r'color="?([^"]+)"?', r"color: \1;", new_params)
                if regex.search(r'size="(.\d*)(?:px)?"', new_params):
                    size = regex.search(r'size="(.\d*)(?:px)?"', new_params).group(1)
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
                    new_params = regex.sub(r'size="(.\d*)(?:px)?"', r"font-size: {};".format(new_size), new_params)
                new_params = regex.sub(r'face="([A-z ]+)"', r"font-family: \1;", new_params)
                new_params = regex.sub(r'style="(.+)"', r"\1", new_params)
                text = regex.sub(r'<font {}>'.format(regex.escape(params)), r'<span style="{}">'.format(new_params), text)
    text = regex.sub(r"(?<!<nowiki>)(?<!<syntaxhighlight)(<\/?)(?:[Ss]trike)>(?!.*?<\/nowiki>)", r"\1s>", text)
    while True:
        if text != regex.sub(r"<center>((?:(?!(?:{\||\|}|(?<!<center>)<\/center>|<\/center>(?=<\/center>)|<\/?gallery>|<center>[^<]*(?!<\/center>[^<]*<\/center>))).)*)<\/center>", r'<div style="text-align: center;">\1</div>', text, flags=regex.DOTALL):
            text = regex.sub(r"<center>((?:(?!(?:{\||\|}|(?<!<center>)<\/center>|<\/center>(?=<\/center>)|<\/?gallery>|<center>[^<]*(?!<\/center>[^<]*<\/center>))).)*)<\/center>", r'<div style="text-align: center;">\1</div>', text, flags=regex.DOTALL)
        else:
            break
    return text
