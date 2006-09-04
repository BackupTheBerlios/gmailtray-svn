# Subclass of "dict", where items can be access by d["key"] or d.key
# (Simplified version of http://feedparser.org)

# Miki Tebeka <miki.tebeka@gmail.com>

class DotDict(dict):
	def __getattr__(self, attr):
		try:
			return self.__dict__[attr]
		except KeyError:
			pass
		try:
			return self[attr]
		except KeyError:
			raise AttributeError(
                "'%s' object has no attribute '%s'" % \
                    (self.__class__.__name__, attr))

	def __setattr__(self, attr, value):
		return self.__setitem__(attr, value)

