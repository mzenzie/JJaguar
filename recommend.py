import descriptions

#Importance of being different in this respect

def a (x):
    print str(x)

def give_rating(profile, lang_to_rate):
    raw_ratings =  sum([float(sum([str(lang_to_rate.get(str(key))) != str(other.get(str(key))) for key, val in lang_to_rate.iteritems() if key not in [u"name", u"description"]])) #List of booleans corresponding to differences
                        * int(profile[u"skills"][other[u"name"]]) #Weight rating by amount of usage of each language.
                        / sum([int(rating) for name, rating in profile[u"skills"].iteritems()]) # sum of ratings for average
                        / len(lang_to_rate.keys()) # number of elements
                for other in [descriptions.evaluated_languages[nomen] for nomen, rate in profile[u"skills"].iteritems() if (nomen != lang_to_rate[u"name"] and rate != 0)]])

    return raw_ratings


# constraints is a map formatted similarly to the programming language maps, e.g.
# {"compiled" : "y", "typing" : "d"} will filter for compiled languages with dynamic typing
def give_recommendations (profile, constraints={}):
    possible_langs = [lang for name, lang in descriptions.evaluated_languages.iteritems()
                      if (name not in profile[u"exceptions"]
                          and False not in [lang.get(key) == val for key, val in constraints.iteritems()])]
    return {lang["name"] : float(give_rating(profile, lang)) for lang in possible_langs}


print give_recommendations({u"name" : u"flerpus", u"skills" : {u"python": u"2", u"java" : u"4", u"clojure" : u"8"}, u"exceptions" : [u"c", u"haskell"]}, {u"vm": u"jvm", u"game" : u"y"})
