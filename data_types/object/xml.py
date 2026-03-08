from core.data_type import DataType
import xml.etree.ElementTree as xml
from utils.loggers import log
from functools import reduce


class XML(DataType):
    data_type_info = {
        "Description": """XML and HTML data (*/xml and */html MIME types)""",
        "Usage notes": """Supply XML/HTML parts under the same root element.
Appropriate Content-Type header is often required by the server.""",
        "Authors": [
            "Vladislav Korchagin @vladko312 https://github.com/vladko312",
        ],
        "Options": [
            "html=False - output data as HTML instead of XML",
            "[html=False] decalration=True - add XML declaration",
            "[html=False] short_empty=False - use <tag /> syntax"
        ],
    }

    def injection_points(self, data, all_injectable=False):
        injs = []
        self.params = self._process_values(data)
        self._deep_injection_points(self.params, 0, injs, [], "", all_injectable)
        return injs

    def _deep_injection_points(self, element, idx, injs, rpath, tpath, all_injectable):
        # Injection points are checked top to bottom: tag, attributes, text, children..., tail
        path = rpath.copy()
        path.append(idx)
        tpath += f".({idx}){element.tag}"
        # TODO: use a custom parser to allow * in tag and attr names (if needed)
        """if self.tag in element.tag:
            injs.append({'field': 'Body', 'part': 'tag name', 'param': f'{tpath[1:]}<*>', "path": path})"""
        for param, value in element.attrib.items():
            ppath = path.copy()
            ppath.append(param)
            """if self.tag in param:
                injs.append({'field': 'Body', 'part': 'attribute name', 'param': f"{tpath[1:]}[{param}]", "path": ppath})"""
            if all_injectable or self.tag in value:
                injs.append({'field': 'Body', 'part': 'attribute value', 'param': f"{tpath[1:]}[{param}]=", 'path': ppath})
        if element.text and (all_injectable or self.tag in element.text):
            injs.append({'field': 'Body', 'part': 'tag text', 'param': f'{tpath[1:]}<>*', 'path': path})
        for idx, value in enumerate(element):
            self._deep_injection_points(value, idx, injs, path, tpath, all_injectable)
        if element.tail and (all_injectable or self.tag in element.tail):
            injs.append({'field': 'Body', 'part': 'tag tail', 'param': f'{tpath[1:]}</>*', 'path': path})

    def _process_values(self, values):
        try:
            parts = [xml.fromstring(x) for x in values]
            res = reduce(xml.Element.extend, parts)
        except (TypeError, xml.ParseError) as e:
            log.log(22, "Invalid XML body parts supplied. Body will be ignored")
            raise e
        return res

    def get_params(self):
        return xml.tostring(self.params,
                            encoding="unicode",
                            method="html" if self.args.get("data_params", {}).get("html", False) else "xml",
                            xml_declaration=self.args.get("data_params", {}).get("decalration", True),
                            short_empty_elements=self.args.get("data_params", {}).get("short_empty", False))

    def inject(self, injection, inj):
        params = xml.fromstring(self.get_params())
        element = params
        for p in inj.get('path')[1:-1]:
            element = element[p]
        if inj.get('part') not in ['attribute value', 'attribute name']:
            element = element[inj.get('path')[-1]]
            if inj.get('part') == "tag name":
                if self.tag in element.tag:
                    element.tag = element.tag.replace(self.tag, injection)
                else:
                    element.tag = injection
            elif inj.get('part') == "tag text" and element.text:
                if self.tag in element.text:
                    element.text = element.text.replace(self.tag, injection)
                else:
                    element.text = injection
            elif inj.get('part') == "tag tail" and element.tail:
                if self.tag in element.tail:
                    element.tail = element.tail.replace(self.tag, injection)
                else:
                    element.tail = injection
        elif inj.get('part') == "attribute name":
            old_value = element.attrib.get(inj.get('path')[-1])
            del element.attrib[inj.get('path')[-1]]
            if self.tag in inj.get('path')[-1]:
                new_param = inj.get('path')[-1].replace(self.tag, injection)
            else:
                new_param = injection
            element.attrib[new_param] = old_value
        elif inj.get('part') == 'attribute value':
            if self.tag in element.attrib.get(inj.get('path')[-1]):
                element.attrib[inj.get('path')[-1]] = element.attrib.get(inj.get('path')[-1]).replace(self.tag, injection)
            else:
                element.attrib[inj.get('path')[-1]] = injection
        return xml.tostring(params,
                            encoding="unicode",
                            method="html" if self.args.get("data_params", {}).get("html", False) else "xml",
                            xml_declaration=self.args.get("data_params", {}).get("decalration", True),
                            short_empty_elements=self.args.get("data_params", {}).get("short_empty", False))
