import re

def format_xpath(xpath_template: str, values: list):
    try:
        keys = re.findall(r"\{(\w+)\}", xpath_template)

        if len(keys) != len(values):
            raise ValueError(
                f"Placeholder count ({len(keys)}) "
                f"does not match values count ({len(values)})"
            )

        mapping = dict(zip(keys, values))

        return xpath_template.format(**mapping)
    except:
        return xpath_template