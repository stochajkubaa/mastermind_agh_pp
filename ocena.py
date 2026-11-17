def ocena(kod, proba):
    trafione_pozycje=0
    trafione_cyfry=0
    
    kod_kopia = list(kod)
    proba_kopia = list(proba)

    for i in range(4):
        if proba_kopia[i] == kod_kopia[i]:
            trafione_pozycje+=1
            kod_kopia[i]= None
            proba_kopia[i]= None

    for i in range(4):
        if proba_kopia[i] is not None and proba_kopia[i] in kod_kopia:
            trafione_cyfry+=1
            kod_kopia[kod_kopia.index(proba_kopia[i])] = None

    return trafione_pozycje, trafione_cyfry
