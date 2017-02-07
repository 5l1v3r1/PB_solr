import argparse
import pysolr
import sys

ID,FORM,LEMMA,UPOS,XPOS,FEAT,HEAD,DEPREL,DEPS,MISC=range(10)

def read_conll(inp,maxsent=0):
    """ Read conll format file and yield one sentence at a time as a list of lists of columns. If inp is a string it will be interpreted as filename, otherwise as open file for reading in unicode"""
    count=0
    sent=[]
    comments=[]
    for line in inp:
        line=line.strip()
        if not line:
            if sent:
                count+=1
                yield sent, comments
                if maxsent!=0 and count>=maxsent:
                    break
                sent=[]
                comments=[]
        elif line.startswith(u"#"):
            if sent:
                raise ValueError("Missing newline after sentence")
            comments.append(line)
            continue
        else:
            sent.append(line.split(u"\t"))
    else:
        if sent:
            yield sent, comments




def add_to_idx(sents,solr,first_id=0,batch=10000):
    """ sents iterates over (tree,comments) """
    docs=[]
    curr_id=first_id
    for tree,comments in sents:
        tags=set()
        for cols in tree:
            tags.add(cols[UPOS])
            if cols[FEAT]!="_":
                for t in cols[FEAT].split("|"):
                    tags.add(t)
            tags.add(cols[DEPREL])
            if cols[DEPS]!="_":
                for g_dtype in cols[DEPS].split("|"):
                    g,dtype=g_dtype.split(":",1)
                    tags.add(dtype)
        txt=" ".join(cols[FORM] for cols in tree)
        docs.append({"id":curr_id, "stext":txt, "tags":list(tags)})
        curr_id+=1
        if len(docs)>=batch:
            solr.add(docs)
            docs=[]
            print("Added at",curr_id,file=sys.stderr,flush=True)
    else:
        if docs:
            solr.add(docs)
        
if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Index CoNLL-U')
    parser.add_argument('--solr', dest='solr', action='store',
                        default="http://localhost:8983/solr/PBCORE",
                        help='Core URL. Default: %(default)s')
    args = parser.parse_args()
    solr=pysolr.Solr(args.solr,timeout=10)
    trees=read_conll(sys.stdin,1000000)
    add_to_idx(trees,solr)
    
    
