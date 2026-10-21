"""SXF reproducible transcription scoring harness (Python 3 stdlib).
Demonstrates WER/CER on SIX SYNTHETIC editorial text pairs.
NO calls to Deepgram, ElevenLabs or any speech-to-text model.
Run: python sxf-stt-evaluation-lab.py
Optional real labeled input: python sxf-stt-evaluation-lab.py your-reviewed-results.csv
Input columns: sample_id,reference,hypothesis; do NOT upload private transcripts.
"""
import csv
import re
import sys

CASES=[
 ("invoice", "please send the invoice to nova labs", "please send an invoice to nova labs"),
 ("spoken-number", "your order number is four two nine", "your order number is 429"),
 ("brand-name", "we use qdrant with elevenlabs transcription", "we use qdrant with eleven labs transcription"),
 ("word-order", "the appointment is on twenty first october", "the appointment is on october twenty first"),
 ("error-code", "the error code is a p i four two", "the error code is api forty two"),
 ("french", "merci beaucoup pour votre aide", "merci beaucoup pour votre aide"),
]

def normalize(text):
    return " ".join(re.sub(r"[^\w\s']", " ", text.casefold()).split())

def distance(a,b):
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        nxt=[i]
        for j,y in enumerate(b,1):
            nxt.append(min(nxt[-1]+1, prev[j]+1, prev[j-1]+(x!=y)))
        prev=nxt
    return prev[-1]

def score(ref,hyp):
    a=normalize(ref); b=normalize(hyp)
    if not a:
        raise ValueError("Reference cannot be empty after normalization")
    return (distance(a.split(),b.split()),len(a.split()),
            distance(list(a),list(b)),len(a))

def main():
    if len(sys.argv)>1:
        with open(sys.argv[1],encoding="utf-8-sig",newline="") as inp:
            reader=csv.DictReader(inp)
            if not {"sample_id","reference","hypothesis"} <= set(reader.fieldnames or []):
                raise ValueError("CSV needs sample_id,reference,hypothesis columns")
            cases=[(r["sample_id"],r["reference"],r["hypothesis"]) for r in reader]
    else:
        cases=CASES
    if not cases: raise ValueError("No rows")
    words=word_errors=chars=char_errors=0
    print("sample_id | WER | CER | ref_words")
    for ident,ref,hyp in cases:
        we,w,ce,c=score(ref,hyp)
        word_errors+=we;words+=w;char_errors+=ce;chars+=c
        print(f"{ident} | {we/w:.3f} | {ce/c:.3f} | {w}")
    print(f"micro WER={word_errors/words:.3f}, micro CER={char_errors/chars:.3f}, samples={len(cases)}")
    if len(sys.argv)==1:
        checks=[(0.143,0.083),(0.429,0.382),(0.333,0.023),
                (0.286,0.381),(0.444,0.156),(0.0,0.0)]
        for (_,a,b),(want_w,want_c) in zip(CASES,checks):
            we,w,ce,c=score(a,b)
            assert round(we/w,3)==want_w and round(ce/c,3)==want_c
        print("SXF synthetic fixture assertions passed. NOT a provider benchmark.")

if __name__=="__main__":
    main()
