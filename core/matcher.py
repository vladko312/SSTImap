from datetime import timedelta
import random

from utils import rand
from utils.loggers import log


def vector(response):
    return {"code": response.status_code, "header_count": len(response.headers), "cookie_count": len(response.cookies),
            "byte_len": len(response.content), "body_len": len(response.text), "body_words": len(response.text.split(" ")),
            "body_lines": len(response.text.split("\n")), "encoding": response.encoding, "redirects": len(response.history),
            "url": response.url.split("?")[0], "time": response.elapsed / timedelta(microseconds=1),
            "content_type": response.headers.get("Content-Type", "unknown"), "server": response.headers.get("Server", "unknown")}


def profile(channel, alphabet=rand.digits):
    channel.req("")
    results = {"code": [], "header_count": [], "cookie_count": [], "byte_len": [], "body_len": [], "body_words": [],
               "body_lines": [], "encoding": [], "redirects": [], "time": [], "url": [], "content_type": [], "server": []}
    useful = len(results)
    for _ in range(channel.args.get("boolean_samples")[0]):
        t, d, v = channel.req(rand.randstr_n(random.randint(channel.args.get("boolean_samples")[1],
                                                            channel.args.get("boolean_samples")[2]), chars=alphabet))
        if not v:
            return {}, {}, False
        for k in v:
            if v[k] not in results[k]:
                results[k].append(v[k])
    site_profile = {}
    site_vector = {}
    allowed_params = ("code,header_count,cookie_count,byte_len,body_len,body_words,body_lines,encoding,redirects,time,"
                      "url,content_type,server" if channel.args.get("boolean_match") in ["", "*", "all"]
                      else channel.args.get("boolean_match")).split(",")
    for k in results:
        if k not in allowed_params:
            # Skipped by user
            site_profile[k] = "skip"
            site_vector[k] = None
            useful -= 1
        elif len(results[k]) == 0:
            # No results
            site_profile[k] = "fail"
            site_vector[k] = None
            useful -= 1
        elif len(results[k]) == 1:
            # Same value every time
            site_profile[k] = "stable"
            site_vector[k] = results[k][0]
        elif (k in ["byte_len", "body_len", "body_words", "body_lines", "time"] and
              ((max(results[k]) - min(results[k])) / sum(results[k]) * len(results[k])) <= channel.args.get("boolean_fuzzy")[0]):
            # Integer value with small variation
            site_profile[k] = "fuzzy"
            site_vector[k] = sum(results[k]) / len(results[k])
        else:
            # Unable to detect pattern in values
            site_profile[k] = "vary"
            site_vector[k] = None
            useful -= 1
    return site_profile, site_vector, useful >= channel.args.get("boolean_match_min")


def match(channel, test_vector):
    if not test_vector:
        log.log(25, f'Unable to match pages, request failed')
        return False
    for k in channel.page_profile:
        if k not in test_vector:
            log.log(25, f'Unable to match pages, missing key: "{k}"')
            return False
        elif channel.page_profile[k] == "stable" and test_vector[k] != channel.page_vector[k]:
            return False
        elif (channel.page_profile[k] == "fuzzy" and
              abs(test_vector[k] - channel.page_vector[k]) / channel.page_vector[k] > channel.args.get("boolean_fuzzy")[1]):
            return False
    return True
