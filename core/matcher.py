from datetime import timedelta
import random

from utils import rand


def vector(response):
    return {"code": response.status_code, "header_count": len(response.headers), "cookie_count": len(response.cookies),
            "byte_len": len(response.content), "body_len": len(response.text), "body_words": len(response.text.split(" ")),
            "body_lines": len(response.text.split("\n")), "encoding": response.encoding, "redirects": len(response.history),
            "url": response.url.split("?")[0], "time": response.elapsed / timedelta(microseconds=1),
            "content_type": response.headers.get("Content-Type", "unknown"), "server": response.headers.get("Server", "unknown")}


def profile(channel, attempts=10, min_size=1, max_size=200, alphabet=rand.digits, fuzzy_limit=0.05, success=7):
    channel.req("")
    results = {"code": [], "header_count": [], "cookie_count": [], "byte_len": [], "body_len": [], "body_words": [],
               "body_lines": [], "encoding": [], "redirects": [], "time": [], "url": [], "content_type": [], "server": []}
    useful = len(results)
    for _ in range(attempts):
        t, d, v = channel.req(rand.randstr_n(random.randint(min_size, max_size), chars=alphabet))
        for k in v:
            if v[k] not in results[k]:
                results[k].append(v[k])
    site_profile = {}
    site_vector = {}
    for k in results:
        if len(results[k]) == 1:
            site_profile[k] = "stable"
            site_vector[k] = results[k][0]
        elif (k in ["byte_len", "body_len", "body_words", "body_lines", "time"] and
              ((max(results[k]) - min(results[k])) / sum(results[k]) * len(results[k])) <= fuzzy_limit):
            site_profile[k] = "fuzzy"
            site_vector[k] = sum(results[k]) / len(results[k])
        else:
            site_profile[k] = "vary"
            site_vector[k] = None
            useful -= 1
    return site_profile, site_vector, useful >= success


def match(channel, test_vector, fuzzy_limit=0.05):
    for k in channel.page_profile:
        if channel.page_profile[k] == "stable" and test_vector[k] != channel.page_vector[k]:
            return False
        elif (channel.page_profile[k] == "fuzzy" and
              abs(test_vector[k] - channel.page_vector[k]) / channel.page_vector[k] > fuzzy_limit):
            return False
    return True
