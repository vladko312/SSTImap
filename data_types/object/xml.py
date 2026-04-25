from core.data_type import DataType
import xml.etree.ElementTree as xml
from utils.loggers import log


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
            "[html=False] declaration=True - add XML declaration",
            "[html=False] short_empty=False - use <tag /> syntax"
        ],
    }

    def injection_points(self, data, all_injectable=False):
        injs = []
        self.params = self._process_values(data)
        self._deep_injection_points(self.params, 0, injs, [], "", all_injectable)
        return injs

    def _deep_injection_points(self, element, idx, injs, rpath, tpath, all_injectable):
        # Injection points are checked top to bottom: attributes, text, children..., tail
        path = rpath.copy()
        path.append(idx)
        tpath += f".({idx}){element.tag}"
        for param, value in element.attrib.items():
            ppath = path.copy()
            ppath.append(param)
            if all_injectable or self.tag in value:
                injs.append({'field': 'Body', 'part': 'attr', 'param': f"{tpath[1:]}[{param}]", 'path': ppath})
        if element.text and (all_injectable or self.tag in element.text):
            injs.append({'field': 'Body', 'part': 'text', 'param': f'{tpath[1:]}/text', 'path': path})
        for idx, value in enumerate(element):
            self._deep_injection_points(value, idx, injs, path, tpath, all_injectable)
        if element.tail and (all_injectable or self.tag in element.tail):
            injs.append({'field': 'Body', 'part': 'tail', 'param': f'{tpath[1:]}/tail', 'path': path})

    def _process_values(self, values):
        try:
            parts = [xml.fromstring(x) for x in values]
            res = parts[0]
            for part in parts[1:]:
                res.extend(part)
        except (TypeError, xml.ParseError) as e:
            log.log(22, "Invalid XML body parts supplied. Body will be ignored")
            raise e
        return res

    def get_params(self):
        return xml.tostring(self.params,
                            encoding="unicode",
                            method="html" if self.args.get("module_params", {}).get("html", False) else "xml",
                            xml_declaration=self.args.get("module_params", {}).get("declaration", True),
                            short_empty_elements=self.args.get("module_params", {}).get("short_empty", False))

    def inject(self, injection, inj):
        params = xml.fromstring(self.get_params())
        element = params
        for p in inj.get('path')[1:-1]:
            element = element[p]
        if inj.get('part') == 'attr':
            if self.tag in element.attrib.get(inj.get('path')[-1]):
                element.attrib[inj.get('path')[-1]] = element.attrib.get(inj.get('path')[-1]).replace(self.tag, injection)
            else:
                element.attrib[inj.get('path')[-1]] = injection
        else:
            element = element[inj.get('path')[-1]]
            if inj.get('part') == "text" and element.text:
                if self.tag in element.text:
                    element.text = element.text.replace(self.tag, injection)
                else:
                    element.text = injection
            elif inj.get('part') == "tail" and element.tail:
                if self.tag in element.tail:
                    element.tail = element.tail.replace(self.tag, injection)
                else:
                    element.tail = injection
        return xml.tostring(params,
                            encoding="unicode",
                            method="html" if self.args.get("module_params", {}).get("html", False) else "xml",
                            xml_declaration=self.args.get("module_params", {}).get("declaration", True),
                            short_empty_elements=self.args.get("module_params", {}).get("short_empty", False))
