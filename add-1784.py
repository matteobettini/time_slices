#!/usr/bin/env python3
"""Add the 1784 Königsberg/Paris slice to both EN and IT JSON files."""
import json

new_en = {
    "year": "1784",
    "title": "Europe — Dare to Know",
    "teaser": "In Königsberg, Kant dares humanity to think for itself. In Paris, a servant outwits his master on stage and a painter resurrects republican Rome. The Enlightenment finds its voice — five years before the guillotine gives it teeth.",
    "dimensions": {
        "art": {
            "label": "Art",
            "content": "Jacques-Louis David is in Rome, painting the work that will remake European art. The <strong>Oath of the Horatii</strong> (completed 1784, exhibited at the Paris Salon 1785) stages three brothers swearing to die for the Roman Republic — rigid, muscular, geometric, the antithesis of Rococo's languid curves. David's <strong>Neoclassicism</strong> isn't nostalgia: it's a political weapon, using antiquity to indict the present. The painting's stark tripartite composition — men on the left reaching for swords, grieving women on the right, the father's outstretched arm at the axis — is rationalism made visible: clarity, duty, structure. When it reaches Paris, the crowds understand instantly. This is what virtue looks like. Five years later, David will paint the Revolution itself."
        },
        "lit": {
            "label": "Literature",
            "content": "<strong>Beaumarchais</strong>' <em>The Marriage of Figaro</em> premieres in Paris on 27 April 1784, after three years of royal censorship — Louis XVI reportedly said it would be \"dangerous\" to perform. He was right. Figaro, a servant, outmanoeuvres, outwits, and publicly humiliates his aristocratic master, Count Almaviva. The fifth-act monologue is a bomb: \"What have you done to deserve such advantages? Put yourself to the trouble of being born — nothing more.\" The theatre is so packed that three people are crushed on opening night. Danton will later say the play \"killed off the nobility\"; Napoleon will call it \"the Revolution already in action.\" Simultaneously in Germany, <strong>Schiller's</strong> <em>Kabale und Liebe</em> (Intrigue and Love) premieres — a bourgeois tragedy exposing aristocratic corruption through a doomed cross-class love affair."
        },
        "phil": {
            "label": "Philosophy",
            "content": "In December 1784, the <em>Berlinische Monatsschrift</em> publishes <strong>Immanuel Kant's</strong> answer to the question that defines the age: <em>\"Was ist Aufklärung?\"</em> — \"What is Enlightenment?\" His answer is a single Latin phrase that becomes a civilisational motto: <strong><em>Sapere aude</em></strong> — \"Dare to know.\" Enlightenment, Kant writes, is humanity's emergence from its \"self-incurred immaturity\" — the inability to use one's own understanding without another's guidance. The obstacle isn't stupidity but cowardice: it is comfortable to let others think for you. Three years earlier, his <strong>Critique of Pure Reason</strong> (1781) had already demolished the old metaphysics, drawing the precise boundary between what reason can and cannot reach. Now he draws the political consequence: think for yourself, in public, without fear."
        },
        "hist": {
            "label": "History",
            "content": "Europe in 1784 is a powder keg with a lit fuse. The <strong>American Revolution</strong> has just succeeded — the Treaty of Paris (1783) confirms it — and French officers who fought there return home full of republican ideals and empty treasury receipts. France's debt from financing American independence is catastrophic; within five years, Louis XVI will be forced to convene the Estates-General. <strong>Frederick the Great</strong> still rules Prussia, Europe's model \"enlightened despot\" — tolerant of religion, patron of Voltaire, yet absolute in power. <strong>Joseph II</strong> of Austria is abolishing serfdom and closing monasteries. The old order is reforming itself frantically, trying to modernise fast enough to survive. It won't be fast enough."
        },
        "conn": {
            "label": "Connections",
            "content": "Everything in 1784 turns on a single tension: <strong>reason against authority</strong>. Kant says: think for yourself. Figaro says: birth is not merit. David paints Roman republicans choosing duty over dynasty. Schiller stages aristocratic power destroying innocent love. Even the \"enlightened despots\" — Frederick, Joseph — embody the paradox: using absolute power to promote freedom, commanding their subjects to be autonomous. The American Revolution has just proved that Enlightenment ideas can topple empires. The French Revolution will soon prove that they can also devour their own children. This is the Enlightenment's high noon — the moment of maximum confidence that reason can rebuild the world. The shadows are already lengthening.",
            "funFact": "Kant famously never left Königsberg in his entire life — yet his essay on Enlightenment, written from that provincial Prussian city, became the defining text of a movement that transformed the planet. The citizens of Königsberg reportedly set their clocks by his daily walk. Reason, apparently, keeps excellent time."
        }
    },
    "sources": [
        {
            "url": "https://en.wikipedia.org/wiki/Answering_the_Question:_What_is_Enlightenment%3F",
            "title": "Kant — What is Enlightenment? — Wikipedia"
        },
        {
            "url": "https://en.wikipedia.org/wiki/The_Marriage_of_Figaro_(play)",
            "title": "The Marriage of Figaro (play) — Wikipedia"
        },
        {
            "url": "https://en.wikipedia.org/wiki/Oath_of_the_Horatii",
            "title": "Oath of the Horatii — Wikipedia"
        },
        {
            "url": "https://en.wikipedia.org/wiki/Intrigue_and_Love",
            "title": "Kabale und Liebe (Intrigue and Love) — Wikipedia"
        },
        {
            "url": "https://en.wikipedia.org/wiki/Age_of_Enlightenment",
            "title": "Age of Enlightenment — Wikipedia"
        },
        {
            "url": "https://en.wikipedia.org/wiki/Neoclassicism",
            "title": "Neoclassicism — Wikipedia"
        }
    ],
    "image": {
        "url": "images/1784-oath-horatii.jpg",
        "caption": "The Oath of the Horatii — Jacques-Louis David, 1784",
        "attribution": "Jacques-Louis David, via Wikimedia Commons / Google Art Project"
    },
    "threads": [
        "rationalism",
        "classical-revival",
        "art-and-power",
        "enlightenment"
    ],
    "location": {
        "lat": 54.7104,
        "lon": 20.4522,
        "place": "Königsberg"
    },
    "addedDate": "2026-02-25"
}

new_it = {
    "year": "1784",
    "title": "Europa — Osa sapere",
    "teaser": "A Königsberg, Kant sfida l'umanità a pensare con la propria testa. A Parigi, un servo beffa il suo padrone in scena e un pittore resuscita la Roma repubblicana. L'Illuminismo trova la sua voce — cinque anni prima che la ghigliottina gli dia i denti.",
    "dimensions": {
        "art": {
            "label": "Arte",
            "content": "Jacques-Louis David è a Roma, intento a dipingere l'opera che rifonderà l'arte europea. Il <strong>Giuramento degli Orazi</strong> (completato nel 1784, esposto al Salon di Parigi nel 1785) mette in scena tre fratelli che giurano di morire per la Repubblica romana — rigidi, muscolosi, geometrici, l'antitesi delle curve languide del Rococò. Il <strong>Neoclassicismo</strong> di David non è nostalgia: è un'arma politica, che usa l'antichità per accusare il presente. La composizione tripartita austera — gli uomini a sinistra protesi verso le spade, le donne in lutto a destra, il braccio teso del padre come asse — è razionalismo reso visibile: chiarezza, dovere, struttura. Quando raggiunge Parigi, la folla capisce immediatamente. Ecco com'è la virtù. Cinque anni dopo, David dipingerà la Rivoluzione stessa."
        },
        "lit": {
            "label": "Letteratura",
            "content": "<em>Le nozze di Figaro</em> di <strong>Beaumarchais</strong> debutta a Parigi il 27 aprile 1784, dopo tre anni di censura reale — Luigi XVI avrebbe detto che metterla in scena sarebbe stato «pericoloso». Aveva ragione. Figaro, un servo, raggira, supera in astuzia e umilia pubblicamente il suo padrone aristocratico, il Conte d'Almaviva. Il monologo del quinto atto è una bomba: «Che avete fatto voi per meritare tanti vantaggi? Vi siete preso la briga di nascere — nient'altro.» Il teatro è così gremito che tre persone vengono schiacciate la sera della prima. Danton dirà che la commedia «uccise la nobiltà»; Napoleone la chiamerà «la Rivoluzione già in azione». Contemporaneamente in Germania, <em>Kabale und Liebe</em> (Intrigo e amore) di <strong>Schiller</strong> va in scena — una tragedia borghese che smaschera la corruzione aristocratica attraverso un amore interclassista destinato alla rovina."
        },
        "phil": {
            "label": "Filosofia",
            "content": "Nel dicembre 1784, la <em>Berlinische Monatsschrift</em> pubblica la risposta di <strong>Immanuel Kant</strong> alla domanda che definisce l'epoca: <em>«Was ist Aufklärung?»</em> — «Che cos'è l'Illuminismo?» La sua risposta è un'unica frase latina che diventa il motto di una civiltà: <strong><em>Sapere aude</em></strong> — «Osa sapere.» L'Illuminismo, scrive Kant, è l'uscita dell'umanità dalla sua «minorità autoimposta» — l'incapacità di servirsi del proprio intelletto senza la guida di un altro. L'ostacolo non è la stupidità ma la vigliaccheria: è comodo lasciare che altri pensino al posto tuo. Tre anni prima, la sua <strong>Critica della ragion pura</strong> (1781) aveva già demolito la vecchia metafisica, tracciando il confine preciso tra ciò che la ragione può e non può raggiungere. Ora ne trae la conseguenza politica: pensa con la tua testa, in pubblico, senza paura."
        },
        "hist": {
            "label": "Storia",
            "content": "L'Europa del 1784 è una polveriera con la miccia accesa. La <strong>Rivoluzione americana</strong> è appena riuscita — il Trattato di Parigi (1783) lo conferma — e gli ufficiali francesi che vi hanno combattuto tornano a casa pieni di ideali repubblicani e con le casse vuote. Il debito della Francia per aver finanziato l'indipendenza americana è catastrofico; entro cinque anni, Luigi XVI sarà costretto a convocare gli Stati Generali. <strong>Federico il Grande</strong> regna ancora sulla Prussia, il modello europeo del «despota illuminato» — tollerante in materia di religione, mecenate di Voltaire, eppure assoluto nel potere. <strong>Giuseppe II</strong> d'Austria sta abolendo la servitù della gleba e chiudendo monasteri. Il vecchio ordine si riforma freneticamente, cercando di modernizzarsi abbastanza in fretta per sopravvivere. Non sarà abbastanza."
        },
        "conn": {
            "label": "Connessioni",
            "content": "Tutto nel 1784 ruota attorno a un'unica tensione: <strong>la ragione contro l'autorità</strong>. Kant dice: pensa con la tua testa. Figaro dice: la nascita non è merito. David dipinge repubblicani romani che scelgono il dovere sulla dinastia. Schiller mette in scena il potere aristocratico che distrugge l'amore innocente. Persino i «despoti illuminati» — Federico, Giuseppe — incarnano il paradosso: usare il potere assoluto per promuovere la libertà, ordinare ai propri sudditi di essere autonomi. La Rivoluzione americana ha appena dimostrato che le idee illuministe possono rovesciare imperi. La Rivoluzione francese dimostrerà presto che possono anche divorare i propri figli. Questo è il mezzogiorno dell'Illuminismo — il momento di massima fiducia che la ragione possa ricostruire il mondo. Le ombre si stanno già allungando.",
            "funFact": "Kant non lasciò mai Königsberg in tutta la sua vita — eppure il suo saggio sull'Illuminismo, scritto da quella città provinciale prussiana, divenne il testo fondante di un movimento che trasformò il pianeta. I cittadini di Königsberg regolavano i loro orologi sulla sua passeggiata quotidiana. La ragione, a quanto pare, tiene un tempo eccellente."
        }
    },
    "sources": [
        {
            "url": "https://it.wikipedia.org/wiki/Risposta_alla_domanda:_che_cos%27%C3%A8_l%27Illuminismo%3F",
            "title": "Kant — Che cos'è l'Illuminismo? — Wikipedia"
        },
        {
            "url": "https://it.wikipedia.org/wiki/Le_nozze_di_Figaro_(commedia)",
            "title": "Le nozze di Figaro (commedia) — Wikipedia"
        },
        {
            "url": "https://it.wikipedia.org/wiki/Il_giuramento_degli_Orazi",
            "title": "Il giuramento degli Orazi — Wikipedia"
        },
        {
            "url": "https://it.wikipedia.org/wiki/Intrigo_e_amore",
            "title": "Intrigo e amore — Wikipedia"
        },
        {
            "url": "https://it.wikipedia.org/wiki/Illuminismo",
            "title": "Illuminismo — Wikipedia"
        },
        {
            "url": "https://it.wikipedia.org/wiki/Neoclassicismo",
            "title": "Neoclassicismo — Wikipedia"
        }
    ],
    "image": {
        "url": "images/1784-oath-horatii.jpg",
        "caption": "Il giuramento degli Orazi — Jacques-Louis David, 1784",
        "attribution": "Jacques-Louis David, via Wikimedia Commons / Google Art Project"
    },
    "threads": [
        "rationalism",
        "classical-revival",
        "art-and-power",
        "enlightenment"
    ],
    "location": {
        "lat": 54.7104,
        "lon": 20.4522,
        "place": "Königsberg"
    },
    "addedDate": "2026-02-25"
}

# Insert into EN
with open('slices.json', 'r') as f:
    en_data = json.load(f)

# Find insertion point (after 1648, before 1889)
insert_idx = None
for i, s in enumerate(en_data):
    if int(s['year']) > 1784:
        insert_idx = i
        break
if insert_idx is None:
    insert_idx = len(en_data)

en_data.insert(insert_idx, new_en)
with open('slices.json', 'w') as f:
    json.dump(en_data, f, indent=2, ensure_ascii=False)
print(f"EN: inserted at index {insert_idx}, total slices: {len(en_data)}")

# Insert into IT
with open('slices.it.json', 'r') as f:
    it_data = json.load(f)

insert_idx_it = None
for i, s in enumerate(it_data):
    if int(s['year']) > 1784:
        insert_idx_it = i
        break
if insert_idx_it is None:
    insert_idx_it = len(it_data)

it_data.insert(insert_idx_it, new_it)
with open('slices.it.json', 'w') as f:
    json.dump(it_data, f, indent=2, ensure_ascii=False)
print(f"IT: inserted at index {insert_idx_it}, total slices: {len(it_data)}")
