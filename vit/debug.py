import pprint

pp = pprint.PrettyPrinter()
pf = pprint.PrettyPrinter(stream=open("/tmp/test",'w'))

def console(*args, **kwargs):
    pp.pprint(*args, **kwargs)

def file(*args, **kwargs):
    pf.pprint(*args, **kwargs)
