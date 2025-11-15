# Die Temporalisierung von Ordnung
## Ein Thesenpapier zur strukturellen Transformation von Informationsarchitekturen

**Stand:** November 2025

---

## Zusammenfassung

Die gegenwärtige Konvergenz unabhängig entwickelter Werkzeuge zur Wissensorganisation – von Obsidian über GitHub bis zu modernen Content-Management-Systemen – deutet auf einen strukturellen Wandel in der Informationsarchitektur hin. Dieses Papier analysiert drei konstitutive Elemente dieser Entwicklung: Plaintext-basierte Datenhaltung, tag-basierte Ordnungsprinzipien und multiple Relationierung. Die zentrale These lautet, dass dieser Wandel nicht primär eine technische Verbesserung darstellt, sondern eine fundamentale Verschiebung in der Zeitlichkeit von Ordnung: von retrospektiven Architekturen, die Entscheidungen des Speicherzeitpunkts konservieren, hin zu prospektiven Architekturen, die Ordnungsoptionen für zukünftige, heute unbekannte Fragen offenhalten.

---

## 1. Phänomenologie der Konvergenz

### 1.1 Beobachtung

In den vergangenen Jahren ist eine bemerkenswerte Konvergenz in der Entwicklung von Werkzeugen zur Wissensorganisation zu beobachten. Unabhängig voneinander entwickelte Systeme laufen auf eine gemeinsame Grundarchitektur zu, die sich durch drei Charakteristika auszeichnet:

1. **Datenhaltung in Plaintext** mit optionaler Markup-Interpretation (typischerweise Markdown)
2. **Tags und Labels** als primäres Ordnungsprinzip anstelle hierarchischer Verzeichnisstrukturen
3. **Multiple Relationierung** durch bidirektionale Verknüpfungen und assoziative Verbindungen

Diese Architektur findet sich in Personal-Knowledge-Management-Werkzeugen wie Obsidian, Logseq und Roam Research, wurde nachträglich in Plattformen wie Notion integriert, prägt zunehmend die Organisationslogik von Entwicklungsumgebungen wie GitHub (wo Labels eine zentrale Rolle bei der Issue- und Pull-Request-Verwaltung spielen), und liegt Content-Management-Systemen wie Kirby zugrunde, die auf Plaintext-Dateien mit YAML-Frontmatter basieren.

### 1.2 Signifikanz

Die Konvergenz ist insofern bemerkenswert, als sie nicht das Ergebnis einer koordinierten Bewegung oder eines dominanten Standards ist. Die genannten Werkzeuge wurden für unterschiedliche Anwendungskontexte entwickelt – persönliches Wissensmanagement, Softwareentwicklung, Content-Publishing – und konvergieren dennoch auf dieselbe strukturelle Lösung.

Dies legt nahe, dass die beobachtete Architektur nicht arbiträr ist, sondern auf ein zugrundeliegendes Problem reagiert, das in verschiedenen Domänen gleichermaßen virulent ist: die Organisation von Information unter Bedingungen von Komplexität, Veränderlichkeit und multiplen Zugangsperspektiven.

---

## 2. Die drei Elemente im Detail

### 2.1 Plaintext als Datenformat

#### Charakteristik

Die Verwendung von Plaintext (ASCII/UTF-8) als primäres Datenformat erscheint zunächst als technische Regression. Moderne Datenformate bieten reichhaltigere Strukturierungsmöglichkeiten, Typisierung und Validierung. Die Rückkehr zu Plaintext verzichtet bewusst auf diese Möglichkeiten.

#### Rationale

Der Verzicht erweist sich bei näherer Betrachtung als strategisch:

**Universelle Lesbarkeit:** Plaintext-Dateien sind ohne spezifische Software lesbar. Ein `cat`-Befehl im Terminal, ein beliebiger Texteditor oder ein einfaches Skript genügen. Diese Eigenschaft ist nicht trivial – sie bedeutet, dass die Daten von ihrer Verarbeitungssoftware unabhängig sind.

**Langzeitstabilität:** Plaintext-Dateien aus den 1970er Jahren sind heute problemlos lesbar. Proprietäre Formate desselben Zeitraums sind häufig nur noch mit archäologischem Aufwand zugänglich. Die Einfachheit des Formats garantiert Lesbarkeit über Jahrzehnte.

**Operationale Effizienz:** Jede Operation auf Plaintext – Suche, Transformation, Versionierung – profitiert von der Einfachheit des Formats. Diff-Algorithmen, reguläre Ausdrücke, Volltextindizierung funktionieren ohne Vorverarbeitung.

**Befreiung von Processing-Silos:** Proprietäre Formate binden Daten an spezifische Verarbeitungssoftware. Plaintext erlaubt die freie Kombination von Werkzeugen. Eine Markdown-Datei kann in Obsidian bearbeitet, mit Pandoc transformiert, in einem Git-Repository versioniert und mit einem statischen Website-Generator publiziert werden.

#### Markdown als Kompromiss

Die Ergänzung durch Markdown-Syntax stellt einen Kompromiss dar: Strukturinformation (Überschriften, Listen, Hervorhebungen) wird in einer Weise codiert, die auch ohne Interpreter menschenlesbar bleibt. Ein Markdown-Dokument ist auch als roher Text verständlich – die Interpretation fügt Darstellung hinzu, aber keine Bedeutung.

### 2.2 Tags als Ordnungsprinzip

#### Das Problem hierarchischer Ordnung

Konventionelle Dateisysteme organisieren Information in Baumstrukturen. Ein Objekt befindet sich an genau einem Ort in der Hierarchie. Diese Struktur impliziert eine 1:1-Relation zwischen Objekt und Position.

Diese Eindeutigkeit, die auf den ersten Blick als Ordnungsleistung erscheint, erweist sich bei komplexeren Wissensbeständen als Restriktion. Ein Dokument, das sowohl für Projekt A als auch für Projekt B relevant ist, muss entweder dupliziert werden (mit den bekannten Problemen der Inkonsistenz) oder einer der beiden Kategorien zugeordnet werden (mit dem Resultat, dass es aus der anderen Perspektive unsichtbar wird).

#### Tags als Auflösung der 1:1-Relation

Tags lösen diese Restriktion auf. Ein Objekt kann beliebig viele Tags tragen. Die Zugehörigkeit zu Kategorien ist nicht mehr exklusiv, sondern kumulativ. Mehrfachzugehörigkeit wird vom Sonderfall zum Normalfall.

Diese scheinbar einfache Änderung hat weitreichende Konsequenzen:

**Ad-hoc-Hierarchien:** Verzeichnisstrukturen können virtuell erzeugt werden, indem nach Tag-Kombinationen gefiltert wird. Die Hierarchie existiert nicht als physische Struktur, sondern als berechnete Sicht.

**Interessegeleitete Ordnung:** Verschiedene Nutzer oder Nutzungskontexte können verschiedene Ordnungen auf denselben Datenbestand projizieren. Die Projektmanagerin sieht die Daten nach Projektzugehörigkeit geordnet, der Compliance-Beauftragte nach Aufbewahrungsfristen, die Forscherin nach thematischen Clustern.

**Explizite statt implizite Semantik:** In einer Hierarchie ergibt sich die Bedeutung eines Objekts aus seiner Position. Der Pfad `/projekte/2024/kunde-x/angebote/` enthält Information über das Objekt, aber diese Information ist im Container gespeichert, nicht im Objekt selbst. Tags machen diese Semantik explizit und portabel.

### 2.3 Multiple Relationierung

#### Über Tags hinaus

Tags etablieren Zugehörigkeiten zu Kategorien. Darüber hinaus ermöglichen moderne Werkzeuge die direkte Verknüpfung von Objekten untereinander – typischerweise durch bidirektionale Links.

Ein bidirektionaler Link bedeutet: Wenn Dokument A auf Dokument B verweist, erscheint dieser Verweis auch in Dokument B als Rückverweis. Die Relation ist symmetrisch sichtbar.

#### Emergente Netzwerkstruktur

Durch die Akkumulation solcher Verknüpfungen entsteht eine Netzwerkstruktur, die zwei Navigationsmodi ermöglicht:

**Assoziative Navigation:** Man kann sich von Objekt zu Objekt entlang der Verknüpfungen bewegen, "Pfaden" folgen, die sich aus den inhaltlichen Beziehungen ergeben.

**Hierarchische Navigation:** Durch Tag-Filterung können weiterhin baumförmige Strukturen erzeugt werden – Themencluster, Projektordner, chronologische Ansichten.

Die Struktur ist damit weder rein hierarchisch noch rein assoziativ, sondern ermöglicht beide Zugangsmodi auf denselben Datenbestand.

---

## 3. Die Asymmetrie von Hierarchie und Tags

### 3.1 Zwei Degradationsmuster

Sowohl hierarchische als auch tag-basierte Systeme unterliegen Degradation. Die Art der Degradation unterscheidet sich jedoch fundamental:

| Dimension | Hierarchische Systeme | Tag-basierte Systeme |
|-----------|----------------------|---------------------|
| **Symptom** | Information wird unfindbar | Information wird mehrdeutig |
| **Mechanismus** | Verschwinden in der Tiefe | Verschwimmen durch Inkonsistenz |
| **Ursache** | Vergessene Speicherlogik | Inkonsistente Benennung |
| **Technisches Problem** | Retrieval | Precision |

**Hierarchien:** Mit zunehmender Tiefe und Breite der Struktur sinkt die Wahrscheinlichkeit, dass ein Suchender die Speicherlogik des ursprünglichen Ablagers rekonstruieren kann. Information "verschwindet" nicht physisch, aber praktisch – sie ist vorhanden, aber nicht auffindbar.

**Tags:** Mit zunehmender Zahl von Beitragenden und zunehmendem Zeitabstand entstehen inkonsistente Benennungen. Synonyme, Schreibvarianten, Bedeutungsverschiebungen führen dazu, dass zusammengehörige Objekte unter verschiedenen Tags abgelegt werden. Die Information "verschwimmt" – sie ist auffindbar, aber unvollständig oder in falsche Kontexte eingebettet.

### 3.2 Die Asymmetrie der Intelligenz

Ein fundamentaler struktureller Unterschied betrifft die Lokalisierung von Ordnungswissen:

**Hierarchische Systeme** speichern Ordnungswissen im Container. Ein Verzeichnis "weiß" etwas über seinen Inhalt – nämlich dass er zu einer bestimmten Kategorie gehört. Das Objekt selbst "weiß" nichts über sich. Wird es verschoben, verliert es seine kategoriale Zugehörigkeit. Das System ist *extern intelligent, intern uninformiert*.

**Tag-basierte Systeme** speichern Ordnungswissen im Objekt. Eine Datei mit Tags trägt ihre kategoriale Zugehörigkeit mit sich. Sie kann in jedem beliebigen Container liegen – oder in gar keinem – ohne Information zu verlieren. Das System ist *intern intelligent, extern agnostisch*.

Diese Asymmetrie hat Konsequenzen für Portabilität und Resilienz: Selbstbeschreibende Objekte können zwischen Systemen migriert werden, ohne Bedeutung zu verlieren. Kontextabhängige Objekte sind an ihre ursprüngliche Umgebung gebunden.

### 3.3 Die kognitive Dynamik

Die praktische Überlegenheit selbstbeschreibender Systeme wird durch eine kognitive Asymmetrie verstärkt:

**Der Speicherkontext** ist bestimmt durch das aktuelle Projekt, die gegenwärtige Fragestellung, die verfügbare Zeit, das momentane Ordnungsverständnis. Die Entscheidung, wo etwas abgelegt wird, reflektiert diesen Kontext und wird in der Struktur eingefroren.

**Der Suchkontext** ist typischerweise ein anderer. Andere Fragestellung, anderer Zeitpunkt, verändertes Verständnis. Die Person, die sucht, ist kognitiv nicht dieselbe wie die Person, die abgelegt hat – selbst wenn es sich physisch um dieselbe Person handelt.

Hierarchische Systeme verlangen, dass der Suchkontext den Speicherkontext rekonstruiert. Das Finden setzt voraus, sich in die Logik des Ablegens zurückzuversetzen. Diese Anforderung ist systematisch schwer zu erfüllen – nicht aufgrund individueller Vergesslichkeit, sondern aufgrund der strukturellen Divergenz zwischen Speicher- und Suchkontext.

Tag-basierte Systeme entkoppeln diese Kontexte. Was abgelegt wird, ist eine Beschreibung *dessen, was das Objekt ist* – nicht *wo es hingehört*. Das "Wo" wird zur Laufzeit berechnet, basierend auf der aktuellen Fragestellung.

---

## 4. Selbstbeschreibung als Paradigmenwechsel

### 4.1 Verteilte vs. lokale Bedeutung

Die vorangegangene Analyse lässt sich auf einen abstrakteren Punkt verdichten:

> In hierarchischen Systemen ist Bedeutung **verteilt** – sie ergibt sich aus der Position in der Struktur.
> 
> In tag-basierten Systemen ist Bedeutung **lokal** – sie ist im Objekt selbst vollständig enthalten.

Diese Unterscheidung ist analog zur Differenz zwischen relationalen Datenbanken (wo die Bedeutung eines Datensatzes sich aus seinen Relationen ergibt) und dokumentenorientierten Datenbanken (wo jedes Dokument selbstbeschreibend ist).

### 4.2 Das Semantic Web: Die richtige Idee, das falsche Mittel

Die Idee selbstbeschreibender Informationseinheiten ist nicht neu. Das Semantic Web, seit den frühen 2000er Jahren vom W3C vorangetrieben, basiert auf demselben Grundgedanken: Informationen sollen so annotiert werden, dass sie ohne Kenntnis des übergeordneten Systems interpretierbar und maschinell verknüpfbar sind.

Das Resource Description Framework (RDF) bildet den formalen Unterbau dieser Vision. Jede Aussage wird als Tripel codiert – Subjekt, Prädikat, Objekt – und damit maschinenlesbar, verknüpfbar, interoperabel. Darauf aufbauend ermöglichen Ontologiesprachen wie OWL (Web Ontology Language) die formale Definition von Konzepten und ihren Beziehungen.

Die Vision war korrekt. Die Implementierung erwies sich jedoch als zu komplex für breite Adoption:

**Formale Ontologien:** Die Definition von Konzepthierarchien und Relationen in OWL erfordert erhebliche Expertise und Vorabplanung.

**Spezielle Serialisierungsformate:** RDF/XML, Turtle, N-Triples – Formate, die weder menschenlesbar noch mit Standardwerkzeugen bearbeitbar sind.

**Inferenzmaschinen:** Um die Möglichkeiten von OWL auszuschöpfen, werden Reasoning-Engines benötigt, die aus expliziten Aussagen implizite ableiten.

**Kognitiver Overhead:** Das Erstellen und Pflegen von RDF-Daten erfordert ein Verständnis formaler Logik, das über alltägliche Wissensarbeit hinausgeht.

Das Resultat: Das Semantic Web ist in spezialisierten Anwendungen angekommen – Linked Open Data im Kulturerbe-Bereich, Wikidata, biomedizinische Ontologien – aber nie in der breiten Praxis der Wissensorganisation.

### 4.3 Die aktuelle Konvergenz als Realisierung der Semantic-Web-Vision

Die hier beschriebene Werkzeuggeneration erreicht funktional ähnliche Effekte wie RDF – Selbstbeschreibung, Verknüpfbarkeit, Interoperabilität – aber mit radikal niedrigerer Einstiegshürde:

| Semantic Web | Aktuelle Werkzeuge |
|--------------|-------------------|
| RDF-Tripel | YAML-Frontmatter, Tags |
| OWL-Ontologien | Emergente Tag-Strukturen |
| SPARQL-Abfragen | Volltextsuche + Filter |
| Formale Inferenz | LLM-gestützte Harmonisierung |

Der entscheidende Unterschied: Die aktuelle Architektur basiert auf Plaintext und menschenlesbaren Konventionen statt auf formalen Sprachen. Eine Markdown-Datei mit YAML-Frontmatter ist sowohl für Menschen als auch für Maschinen lesbar – ohne Spezialwerkzeuge, ohne Vorwissen über formale Ontologien.

Man könnte formulieren: Die aktuelle Werkzeuggeneration realisiert die Vision des Semantic Web mit den Mitteln menschlicher Alltagspraxis statt formaler Wissensrepräsentation. Oder, aus einer anderen Perspektive: Sie realisiert die Vision des Semantic Web mit den Mitteln der Unix-Philosophie – Plaintext, kleine Werkzeuge, Kompositionsfähigkeit.

### 4.4 Konsequenzen

**Portabilität:** Eine Markdown-Datei mit YAML-Frontmatter funktioniert in Obsidian, in einem Git-Repository, als Input für einen statischen Website-Generator, oder gelesen mit einem beliebigen Texteditor. Die Bedeutung ist nicht an ein System gebunden.

**Resilienz:** Wenn das verwaltende System wegfällt, bleiben selbstbeschreibende Daten verständlich. Proprietäre Datenbanken sterben mit ihrer Software. Plaintext mit Metadaten überlebt die Softwaregenerationen, die es verarbeiten.

**Kompositionsfähigkeit:** Selbstbeschreibende Einheiten können zu neuen Strukturen kombiniert werden, die bei ihrer Erstellung nicht vorgesehen waren. Das ist die technische Grundlage von Assoziativität: Verbindungen entstehen ad hoc, nicht nach Plan.

**Anschlussfähigkeit an LOD:** Die Verknüpfung mit Linked-Open-Data-Ressourcen (GND, Getty AAT, Wikidata) kann als nachträgliche Mapping-Schicht hinzugefügt werden – ohne dass die Daten von Anfang an in RDF modelliert werden müssen.

### 4.5 Verdichtete Formulierung

> Hierarchien speichern Position. Tags speichern Bedeutung. Position ist fragil, Bedeutung ist portabel.

---

## 5. Einwände und Abwägungen

### 5.1 Skalierung

**Einwand:** Bei sehr großen Datenbeständen werden flache Strukturen mit Tags ineffizient – sowohl für menschliche Navigation als auch für maschinelle Verarbeitung.

**Abwägung:** Dieser Einwand verwechselt konzeptionelle Eigenschaften mit Implementierungsdetails. Skalierungsprobleme sind durch etablierte Techniken lösbar: Hashing für konstante Zugriffszeiten, Indizierung für effiziente Suche, Caching für häufige Abfragen.

Die relevante Frage ist nicht, ob flache Strukturen bei Millionen von Objekten effizient implementierbar sind (sie sind es), sondern ob Menschen mit solchen Beständen arbeiten können. Hier liegt das eigentliche Problem – aber es ist kein Problem der Tag-Architektur per se, sondern ein Problem der Werkzeuggestaltung.

### 5.2 Governance und Compliance

**Einwand:** Regulierte Branchen erfordern definierte Taxonomien, nachvollziehbare Audit-Trails und rechtlich verbindliche Versionierung. Eine emergente Tag-Struktur kann diese Anforderungen nicht erfüllen.

**Abwägung:** Dieser Einwand übersieht, dass Governance-Anforderungen nicht die Abschaffung von Tags erfordern, sondern ihre Disziplinierung. Regulatorische Kategorien (Aufbewahrungsfristen, Vertraulichkeitsstufen, Compliance-Relevanz) können als Tags implementiert werden – mit dem Unterschied, dass sie nicht emergent entstehen, sondern aus einem kontrollierten Vokabular stammen.

Die hierarchische Perspektive wird damit nicht abgeschafft, sondern zu einer von mehreren möglichen Sichten auf denselben Datenbestand. Die Daten bleiben im Pool; die Compliance-Sicht ist eine Projektion auf Basis spezifischer Tags.

### 5.3 Tag-Drift und Inkonsistenz

**Einwand:** Bei vielen Beitragenden entstehen unweigerlich inkonsistente Benennungen: Synonyme, Schreibvarianten, Bedeutungsverschiebungen. Ohne ontologische Vorabdefinition oder aufwendige Governance degradiert der Datenpool zur "Tag-Suppe".

**Abwägung:** Dieser Einwand trifft. Die Folksonomy-Forschung der 2000er Jahre (Del.icio.us, Flickr) hat gezeigt, dass rein emergente Tag-Systeme ohne jede Governance zur Inkonsistenz tendieren.

Allerdings ist die Alternative – hierarchische Ablage – nicht immun gegen Degradation. Sie degradiert nur anders: nicht durch Inkonsistenz, sondern durch Unzugänglichkeit. Information verschwindet in der Tiefe statt zu verschwimmen.

Die relevante Frage ist daher nicht, welches System frei von Degradation ist (keines ist es), sondern welches Degradationsmuster leichter zu kompensieren ist – und welche neuen Möglichkeiten der Kompensation heute verfügbar sind.

---

## 6. Die Frage der Novität

### 6.1 Der berechtigte Einwand

Die Informationswissenschaft hat die hier beschriebenen Konzepte seit Jahrzehnten untersucht. Faceted Classification geht auf S.R. Ranganathan in den 1930er Jahren zurück. Die Folksonomy-Forschung der 2000er Jahre hat Tag-Systeme empirisch analysiert. Das Semantic Web hat selbstbeschreibende Daten als Architekturprinzip formuliert.

Was also könnte an der gegenwärtigen Entwicklung neu sein?

### 6.2 Drei Kandidaten für genuine Beiträge

#### 6.2.1 Die Auflösung der Speicher-Such-Asymmetrie

Historisch waren Speichern und Suchen getrennte Operationen mit unterschiedlichen Optimierungszielen. Organisation war notwendig, *weil* Suche teuer war. Man investierte Aufwand beim Speichern, um Aufwand beim Suchen zu sparen.

Die radikale Verbilligung von Suche – durch Volltextindizierung, semantische Suche, und zuletzt durch Large Language Models – verändert diese Ökonomie grundlegend. Wenn Suche nahezu kostenlos ist, verliert Organisation ihre instrumentelle Rechtfertigung.

**These:** Wir erleben nicht die Ablösung einer Organisationsform durch eine bessere, sondern das *Ende von Organisation als Notwendigkeit*. Tags sind dann keine Alternative zu Hierarchien, sondern eine Beschreibungssprache für Objekte, die gar nicht mehr "organisiert" werden müssen.

Die Informationswissenschaft hat diese Möglichkeit kaum systematisch erwogen, weil sie von der Prämisse ausgeht, dass Organisation notwendig ist.

#### 6.2.2 Die Emergenz von Struktur aus Beschreibung

Die klassische Reihenfolge in der Informationsverarbeitung ist:
1. Struktur definieren (Schema, Ontologie, Taxonomie)
2. Daten einfügen (gemäß der definierten Struktur)
3. Abfragen (innerhalb der definierten Struktur)

Die emergente Reihenfolge ist:
1. Daten beschreiben (durch Tags, Metadaten, Verknüpfungen)
2. Abfragen (nach beliebigen Kriterien)
3. Struktur erzeugen (als Resultat der Abfrage)

**These:** Struktur wird von etwas Gegebenem zu etwas Berechnetem. Sie existiert nicht als persistente Eigenschaft des Datenbestands, sondern entsteht im Moment der Abfrage und vergeht mit ihr.

Diese Temporalisierung von Struktur hat Konsequenzen, die möglicherweise nicht vollständig expliziert sind: Was bedeutet "Ordnung" in einem System, in dem Ordnung nicht existiert, sondern geschieht?

#### 6.2.3 Redundanz als Optionalität

Hierarchische Systeme erzwingen Eindeutigkeit: Ein Objekt hat einen Ort. Redundanz gilt als problematisch – sie erzeugt Inkonsistenzrisiken und Speicherkosten.

In tag-basierten Systemen ist Mehrfachzugehörigkeit konstitutiv. Jeder zusätzliche Tag ist ein potenzieller Zugangsweg. Redundanz wird zum Feature: Sie speichert *Optionalität* – Möglichkeiten des Zugangs, die heute nicht genutzt werden, aber morgen relevant werden können.

**These:** Die informationstheoretische Bewertung von Redundanz ändert sich in selbstbeschreibenden Systemen. Redundanz ist nicht Rauschen, sondern gespeichertes Potenzial.

Fragen, die sich anschließen: Gibt es einen formalen Zusammenhang zwischen der Anzahl der Tags pro Objekt und seiner Findbarkeit? Wie verhält sich die Entropie eines tag-basierten Systems zu der eines hierarchischen?

---

## 7. Synthese: Die Temporalisierung von Ordnung

### 7.1 Der gemeinsame Kern

Die drei Kandidaten für Novität lassen sich auf einen gemeinsamen Kern zurückführen:

- 6.2.1 sagt: Organisation wird optional, weil Suche gut genug ist.
- 6.2.2 sagt: Struktur entsteht zur Laufzeit, nicht vorab.
- 6.2.3 sagt: Mehrfachzugehörigkeit hält Optionen offen.

Was verbindet diese Aussagen?

**Die Verlagerung von Ordnung aus der Vergangenheit in die Gegenwart.**

### 7.2 Retrospektive vs. prospektive Architekturen

Hierarchische Systeme sind *retrospektiv*: Sie konservieren eine Ordnungsentscheidung, die zum Zeitpunkt des Speicherns getroffen wurde. Die Struktur ist ein Artefakt vergangener Intentionen. Suche bedeutet, sich in diese vergangene Logik zurückzuversetzen.

Tag-basierte, selbstbeschreibende Systeme sind *prospektiv*: Sie halten Ordnungsoptionen offen für zukünftige, heute unbekannte Fragen. Die Struktur entsteht im Moment der Abfrage, geprägt durch den gegenwärtigen Kontext, nicht den vergangenen.

### 7.3 Eine andere Zeitlichkeit von Information

Diese Unterscheidung ist nicht primär technisch. Sie betrifft das Verhältnis von Information und Zeit.

In retrospektiven Architekturen ist Ordnung etwas *Gegebenes* – ein Zustand, der durch vergangene Entscheidungen hergestellt wurde und in der Gegenwart vorgefunden wird.

In prospektiven Architekturen ist Ordnung etwas *Werdendes* – ein Prozess, der in der Gegenwart stattfindet und durch gegenwärtige Fragen ausgelöst wird.

**Zentrale These:**

> Der strukturelle Kern der gegenwärtigen Transformation von Informationsarchitekturen ist die Verschiebung von retrospektiver zu prospektiver Ordnung – von Struktur als Artefakt zu Struktur als Ereignis.

---

## 8. Die Rolle von Large Language Models

### 8.1 Das historische Dilemma

Die Folksonomy-Forschung hat ein Dilemma identifiziert:

**Top-down (Taxonomie):** Kontrollierte Vokabulare gewährleisten Konsistenz, erfordern aber erheblichen Governance-Aufwand und skalieren schlecht mit der Zahl der Beitragenden und der Dynamik des Wissensgebiets.

**Bottom-up (Folksonomy):** Emergente Tag-Systeme sind flexibel und skalieren gut, tendieren aber zur Inkonsistenz ("Tag-Suppe").

Keiner der beiden Ansätze löst das Problem vollständig. Top-down ist zu rigide, bottom-up ist zu chaotisch.

### 8.2 Eine neue Möglichkeit

Large Language Models eröffnen einen dritten Weg: *Post-hoc-Harmonisierung*.

LLMs können:
- Implizite Ontologien in einem Tag-Bestand explizit machen
- Synonyme und Schreibvarianten erkennen und zusammenführen
- Hierarchische Beziehungen zwischen Tags vorschlagen
- Inkonsistenzen flaggen und Korrekturvorschläge generieren
- Tagging-Vorschläge auf Basis des Inhalts generieren

Damit wird eine dritte Option denkbar:

**Emergent + harmonisiert:** Tags entstehen aus der Praxis der Beitragenden (bottom-up), werden aber kontinuierlich durch KI-gestützte Analyse harmonisiert (ohne zentrale Governance).

### 8.3 Bedeutung für die These

Die Kombination aus:
1. Flacher Datenstruktur (Plaintext + Metadaten)
2. Multipler Relationierung (Tags, Links)
3. KI-gestützter Konsistenzpflege

könnte das historische Dilemma zwischen Taxonomie und Folksonomy auflösen.

Dies ist ein Beitrag, der 2015 nicht hätte formuliert werden können. Die technische Möglichkeit, emergente Strukturen ohne zentrale Governance zu harmonisieren, ist neu.

---

## 9. Anwendungsfall: Kontrollierte Vokabulare im Kulturerbe-Bereich

### 9.1 Der klassische Ansatz

Projekte zur Entwicklung kontrollierter Vokabulare – etwa Thesauri für Sammlungen im Kulturerbe-Bereich – folgen typischerweise dem Top-down-Paradigma:

1. Expert*innen definieren kollaborativ ein Vokabular
2. Das Vokabular wird nach Standards (ISO 25964) strukturiert
3. Die Ergebnisse werden mit bestehenden Normdaten (GND, Getty AAT, Wikidata) verknüpft
4. Die Sammlungen erschließen ihre Objekte mit dem definierten Vokabular

Dieser Ansatz erfordert erheblichen Koordinationsaufwand. Typischerweise werden Workshop-Reihen über mehrere Jahre organisiert, um die notwendige interdisziplinäre Abstimmung zu erreichen.

### 9.2 Die Herausforderung

Die Expertise liegt verteilt bei den einzelnen Sammlungen. Jede Sammlung hat ihre eigene Begriffspraxis, die sich aus ihrer Geschichte, ihrem Sammlungsprofil und ihrer Fachkultur ergibt. Der Thesaurus ist der Versuch, diese verteilte Praxis zu vereinheitlichen.

Das Problem: Die Vereinheitlichung muss *vor* der Erschließung stattfinden. Die Sammlungen können erst mit der standardisierten Erfassung beginnen, wenn das Vokabular definiert ist. Das erzeugt Wartezeiten und Reibungsverluste.

### 9.3 Eine alternative Perspektive

Der hier entwickelte Ansatz legt eine andere Reihenfolge nahe:

1. Die Sammlungen erfassen ihre Objekte mit ihrer *eigenen* Begriffspraxis
2. Die Begriffspraktiken werden gesammelt und analysiert
3. Synonyme, Überlappungen und implizite Hierarchien werden (ggf. KI-gestützt) identifiziert
4. Der Thesaurus *entsteht* aus der Praxis, statt ihr voranzugehen

Das würde bedeuten:
- Die Erschließung kann sofort beginnen, ohne auf das Vokabular zu warten
- Das Vokabular reflektiert die tatsächliche Begriffspraxis statt normativ gesetzter Kategorien
- Die Interoperabilität mit Normdaten entsteht durch Mapping, nicht durch Vorab-Einpassung

### 9.4 FAIR-Prinzipien und Selbstbeschreibung

Die FAIR-Prinzipien (Findable, Accessible, Interoperable, Reusable) verlangen im Kern selbstbeschreibende Daten. Ein Objekt soll ohne Kenntnis des übergeordneten Systems interpretierbar sein.

Ein Objekt, dessen Bedeutung sich aus seiner Position in einer Sammlungshierarchie ergibt, ist weniger FAIR als eines, das seine Kategorisierung explizit als Metadaten trägt.

Tag-basierte Erschließung ist damit nicht nur kompatibel mit FAIR, sondern ihr konstitutiv näher als hierarchische Erschließung.

### 9.5 Linked Open Data als Brücke

Die Verlinkung lokaler Begriffe mit globalen Normdaten (GND, Getty AAT, Wikidata) ist im Kern ein Mapping-Problem: Wie wird die lokale Begriffspraxis einer Sammlung in ein übergreifendes Vokabular übersetzt?

Dieses Mapping muss nicht flächendeckend und vorab erfolgen. Es kann punktuell und on-demand geschehen: Wenn eine Sammlung einen ihrer Begriffe mit einem GND-Eintrag verknüpft, entsteht Interoperabilität für diesen Begriff. Die Verknüpfungen akkumulieren sich über Zeit.

Der pragmatische Mittelweg: Die Sammlungen arbeiten mit einfachen, selbstbeschreibenden Formaten (Plaintext, Tags, YAML). Die Interoperabilität mit der Linked-Open-Data-Welt entsteht durch nachträgliches Mapping auf RDF – nicht durch Vorab-Modellierung in RDF. Die Komplexität des Semantic Web wird zur optionalen Export-Schicht, nicht zur Voraussetzung für die tägliche Arbeit.

---

## 10. Forschungsfragen

Die vorangegangene Analyse eröffnet mehrere Forschungsrichtungen:

### 10.1 Empirische Fragen

1. Unter welchen Bedingungen übertrifft eine tag-basierte Architektur eine hierarchische hinsichtlich Retrieval-Qualität?
2. Wie entwickelt sich Tag-Konsistenz über Zeit in Systemen mit/ohne KI-gestützte Harmonisierung?
3. Welche minimalen Beschreibungsanforderungen muss ein Objekt erfüllen, um für unbekannte zukünftige Fragen findbar zu bleiben?

### 10.2 Theoretische Fragen

1. Wie lässt sich die Unterscheidung retrospektiv/prospektiv informationstheoretisch formalisieren?
2. Gibt es einen formalen Zusammenhang zwischen Tag-Redundanz und Findbarkeit?
3. Welche Eigenschaften muss ein System haben, damit Struktur als "berechnet" statt "gegeben" gelten kann?

### 10.3 Gestaltungsfragen

1. Wie müssen Werkzeuge gestaltet sein, die prospektive Informationsarchitekturen unterstützen?
2. Welche Formen von KI-gestützter Harmonisierung sind effektiv, ohne die Flexibilität emergenter Systeme zu zerstören?
3. Wie lassen sich die Vorteile kontrollierter Vokabulare mit der Flexibilität emergenter Tags kombinieren?

---

## 11. Theoretische Anschlüsse

Die entwickelten Thesen sind anschlussfähig an mehrere Forschungstraditionen:

### 11.1 Kognitionswissenschaft

Die Prototypentheorie (Rosch) zeigt, dass menschliche Kategorisierung nicht durch notwendige und hinreichende Bedingungen funktioniert, sondern durch Familienähnlichkeiten und prototypische Beispiele. Tag-basierte Systeme bilden diese Struktur besser ab als hierarchische Taxonomien.

Spreading-Activation-Modelle des Gedächtnisses beschreiben Erinnerung als assoziative Aktivierung in einem Netzwerk. Die Netzwerkstruktur, die durch bidirektionale Links entsteht, korrespondiert dieser Modellierung.

### 11.2 Prozessphilosophie

Die Unterscheidung zwischen Struktur als Gegebenem und Struktur als Werdendem korrespondiert der prozessphilosophischen Unterscheidung zwischen Substanz und Ereignis (Whitehead). Information wäre dann nicht primär ein Bestand, sondern ein Prozess.

### 11.3 Informationstheorie

Die Neubewertung von Redundanz – nicht als Rauschen, sondern als Optionalität – erfordert möglicherweise eine Revision informationstheoretischer Grundbegriffe. Die Entropie eines tag-basierten Systems könnte anders zu messen sein als die eines hierarchischen.

### 11.4 Bibliotheks- und Informationswissenschaft

Die Faceted-Classification-Tradition (Ranganathan) hat die Grundlagen für nicht-hierarchische Ordnung gelegt. Die hier beschriebene Entwicklung kann als technische Realisierung dieser Tradition unter veränderten technologischen Bedingungen verstanden werden.

---

## 12. Schluss

Die Konvergenz aktueller Werkzeuge zur Wissensorganisation auf eine gemeinsame Architektur – Plaintext, Tags, multiple Relationierung – ist kein Zufall. Sie reagiert auf ein strukturelles Problem: die Inadäquatheit retrospektiver Ordnungssysteme für Wissensbestände, die unter Bedingungen von Komplexität, Veränderlichkeit und multiplen Zugangsperspektiven verwaltet werden müssen.

Die zentrale These dieses Papiers lautet, dass der beobachtete Wandel über eine technische Verbesserung hinausgeht. Er markiert eine Verschiebung in der Zeitlichkeit von Ordnung: von Strukturen, die vergangene Entscheidungen konservieren, zu Strukturen, die im Moment der Abfrage entstehen.

Diese Verschiebung wird ermöglicht durch die radikale Verbilligung von Suche und – prospektiv – durch die Möglichkeit KI-gestützter Harmonisierung emergenter Strukturen.

Die praktischen Implikationen betreffen die Gestaltung von Werkzeugen, die Konzeption von Erschließungsprojekten im Kulturerbe-Bereich und darüber hinaus jede Domäne, in der Information organisiert werden muss.

Die theoretischen Implikationen betreffen das Verständnis dessen, was "Ordnung" in Informationssystemen bedeutet – und möglicherweise darüber hinaus das Verhältnis von Information, Struktur und Zeit.

---

## Literatur

*(Ausgewählte Referenzen zur Vertiefung)*

**Faceted Classification:**
- Ranganathan, S.R. (1967): Prolegomena to Library Classification. Asia Publishing House.

**Folksonomy-Forschung:**
- Shirky, C. (2005): Ontology is Overrated: Categories, Links, and Tags.
- Golder, S.A. & Huberman, B.A. (2006): Usage Patterns of Collaborative Tagging Systems. Journal of Information Science.

**Semantic Web:**
- Berners-Lee, T., Hendler, J. & Lassila, O. (2001): The Semantic Web. Scientific American.
- W3C (2014): RDF 1.1 Primer. https://www.w3.org/TR/rdf11-primer/
- W3C (2012): OWL 2 Web Ontology Language Primer. https://www.w3.org/TR/owl2-primer/

**Personal Knowledge Management:**
- Matuschak, A.: Evergreen Notes. https://notes.andymatuschak.org/

**Kognitionswissenschaft:**
- Rosch, E. (1975): Cognitive Representations of Semantic Categories. Journal of Experimental Psychology.
- Lakoff, G. (1987): Women, Fire, and Dangerous Things. University of Chicago Press.

**Information Architecture:**
- Morville, P. & Rosenfeld, L. (2006): Information Architecture for the World Wide Web. O'Reilly.

**FAIR-Prinzipien:**
- Wilkinson, M.D. et al. (2016): The FAIR Guiding Principles for scientific data management and stewardship. Scientific Data.

**Unix-Philosophie:**
- Raymond, E.S. (2003): The Art of Unix Programming. Addison-Wesley.

---

*Dieses Papier ist als Diskussionsgrundlage konzipiert und erhebt keinen Anspruch auf Vollständigkeit der Argumentation oder der Literaturbasis.*
