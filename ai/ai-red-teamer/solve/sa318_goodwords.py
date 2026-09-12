#!/usr/bin/env python3
# Module 318 Skills Assessment: two-phase GoodWords via black-box /predict (no unpickling).
import os, requests
B=os.environ["BASE_URL"]
S=requests.Session()

NEG=("awful terrible horrible boring worst bad disappointing dull tedious lame poor bland "
     "forgettable mediocre unwatchable pathetic garbage waste stupid annoying pointless painful "
     "cringe atrocious disaster failure worse mess nonsense horrible dreadful lifeless clumsy "
     "amateurish incoherent unbearable disgusting ridiculous embarrassing").split()
POS=("excellent amazing wonderful brilliant fantastic masterpiece superb perfect beautiful "
     "outstanding love loved great best delightful enjoyable remarkable captivating gem flawless "
     "stunning moving inspiring memorable charming gripping compelling heartwarming magnificent "
     "phenomenal exceptional terrific marvelous engaging riveting").split()

def predict(text):
    r=S.post(f"{B}/predict",json={"text":text},timeout=20).json()
    return r

def score(text, want):  # probability of desired class
    r=predict(text)
    return r["negative_probability"] if want=="negative" else r["positive_probability"], r["label"]

def rank(words, base_text, want):
    bp,_=score(base_text,want)
    imp=[]
    for w in words:
        p,_=score(base_text+" "+w, want)
        imp.append((w,p-bp))
    imp.sort(key=lambda x:x[1],reverse=True)
    return [w for w,_ in imp]

def attack(reviews, want, budget, cand):
    sols=[]
    for rv in reviews:
        text=rv["text"]
        ranked=rank(cand, text, want)          # per-review ranking
        # sequence: diverse top words first, then fill with the single strongest word repeated
        seq=ranked[:budget] + [ranked[0]]*budget
        added=0; aug=text; flipped=False
        for w in seq:
            if added>=budget: break
            aug=aug+" "+w; added+=1
            p,lab=score(aug,want)
            if lab==want:
                flipped=True; break
        sols.append({"id":rv["id"],"augmented_text":aug,"_flipped":flipped,"_added":added})
    for s in sols:
        print("  ",s["id"],"flipped",s["_flipped"],"added",s["_added"])
    return [{"id":s["id"],"augmented_text":s["augmented_text"]} for s in sols]

def run_phase(phase, want, budget, cand):
    ch=S.get(f"{B}/challenge/{phase}",timeout=20).json()
    reviews=ch["reviews"]; budget=int(ch.get("max_added_words",budget))
    print(f"[{phase}] reviews={len(reviews)} budget={budget}")
    sols=attack(reviews, want, budget, cand)
    res=S.post(f"{B}/submit/{phase}",json={"solutions":sols},timeout=30).json()
    print(f"[{phase}] result:", str(res)[:400])
    return res

print("health", S.get(f"{B}/health",timeout=10).json())
r1=run_phase("whitebox","negative",30,NEG)
r2=run_phase("blackbox","positive",40,POS)
print("STATUS", S.get(f"{B}/status",timeout=10).json())
