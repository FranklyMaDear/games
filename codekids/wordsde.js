const WORDS_DE = [
    // ====== DEUTSCHE MÄRCHEN ======
    { word: "ROTKÄPPCHEN", hint: "Ein Mädchen mit einer roten Mütze, das der Großmutter Kuchen im Wald bringt." },
    { word: "ASCHENPUTTEL", hint: "Ein Mädchen verliert einen gläsernen Schuh auf dem Ball im Schloss." },
    { word: "SCHNEEWITTCHEN", hint: "Eine Prinzessin schläft tief, nachdem sie in einen giftigen Apfel gebissen hat." },
    { word: "RAPUNZEL", hint: "Eine Prinzessin mit sehr langen goldenen Haaren lebt in einem hohen Turm." },
    { word: "RUMPELSTILZCHEN", hint: "Ein kleines Männchen tanzt um ein Feuer und niemand weiß seinen Namen." },
    { word: "HÄNSEL UND GRETEL", hint: "Zwei Geschwister finden im Wald ein Haus aus süßem Lebkuchen." },

    // ====== KINDERFERNSEHEN & CHARAKTERE ======
    { word: "MAUS", hint: "Ein schlaues, orangefarbenes Tier zeigt sonntags Lach- und Sachgeschichten im Fernsehen." },
    { word: "ELEFANT", hint: "Ein kleiner, blauer Riese mit Rüssel, der im Fernsehen zu sehen ist." },
    { word: "PUMUCKL", hint: "Ein kleiner, rothaariger Kobold, der unsichtbar sein kann und in einer Werkstatt wohnt." },
    { word: "TABALUGA", hint: "Ein kleiner, grüner Drache, der fliegen lernen muss und seine Heimat beschützt." },
    { word: "BENJAMIN BLÜMCHEN", hint: "Ein sprechender Grauhäuter aus dem Zoo, der gerne Zuckerstückchen frisst und ein lautes Geräusch macht." },
    { word: "BIBI BLOCKSBERG", hint: "Ein junges Mädchen aus Neustadt, das auf einem Besen reiten und zaubern kann." },
    { word: "SAMS", hint: "Ein Wesen mit roten Haaren und blauen Punkten im Gesicht bringt den Menschen Glück." },
    { word: "KIKA", hint: "Ein bekannter Fernsehsender im deutschen Fernsehen nur für Kinder." },
    { word: "BERND DAS BROT", hint: "Ein sehr deprimiertes, kastenförmiges Gebäck mit kurzen Armen im Fernsehen." },
    { word: "LÖWENZAHN", hint: "Eine Sendung über Natur und Technik mit einem Mann, der in einem blauen Bauwagen im Garten wohnt." },
    { word: "BAUWAGEN", hint: "Ein mobiles Haus auf Rädern, in dem Fritz Fuchs mit seinem Hund Keks wohnt und Sachen erklärt." },
    { word: "LOGO", hint: "Die bekannten Nachrichten auf KiKa, die aktuelle Themen aus aller Welt einfach für Jugendliche erklären." },
    { word: "PUR PLUS", hint: "Ein Magazin im Fernsehen, bei dem Eric spannende Experimente macht und wichtige Fragen beantwortet." },
    { word: "CHILI DAS SCHAF", hint: "Ein sehr aktives, gelbes Wolltier mit Sonnenbrille, das oft mit Bernd dem Brot im Fernsehen zu sehen ist." },
    { word: "BRIEGEL", hint: "Ein grüner, sprechender Busch, der gerne verrückte Erfindungen baut, die fast immer explodieren." },
    { word: "WISSEN MACHT AAH", hint: "Eine lustige Lernsendung mit Shary und Ralph, die schwierige Dinge mit viel Humor erklären." },
    { word: "FEUERWEHRMANN SAM", hint: "Ein tapferer Retter in einer blauen Uniform, der den Menschen in einer kleinen Stadt bei Unfällen hilft." },
    { word: "WICKIE", hint: "Ein kleiner, schlauer Junge mit einem Helm, der immer eine gute Idee hat, wenn er sich an der Nase reibt." },

    // ====== KINDERBÜCHER & HELDEN ======
    { word: "PIPPI LANGSTRUMPF", hint: "Ein sommersprossiges Mädchen mit roten Zöpfen lebt allein in einer bunten Villa." },
    { word: "URMEL", hint: "Ein kleines grünes Urzeitwesen schlüpft auf einer Insel aus einem Ei." },
    { word: "GRÜFFELO", hint: "Ein großes Waldmonster mit feurigen Augen und Stacheln hat Angst vor einer kleinen Maus." },
    { word: "CONNI", hint: "Ein Mädchen mit einer roten Schleife im Haar erlebt viele Alltagsabenteuer." },
    { word: "MOMO", hint: "Ein kleines Mädchen in einer Jacke kämpft gegen die grauen Herren, um den Menschen die gestohlene Zeit zurückzugeben." },
    { word: "PETTERSSON", hint: "Ein alter, freundlicher Mann mit Hut lebt auf einem Bauernhof und baut tolle Sachen für seinen kleinen Kater." },
    { word: "FINDUS", hint: "Ein kleiner, frecher Kater mit einer grünen Hose, der sprechen kann und am liebsten Geburtstagskuchen isst." },
    { word: "JIM KNOPF", hint: "Ein kleiner Junge wohnt auf einer Insel mit zwei Bergen und reist mit einer Lokomotive namens Emma." },
    { word: "LUMMERLAND", hint: "Eine winzige Insel im Ozean mit zwei Bergen, auf der nur eine Lokomotive und vier Menschen wohnen." },
    { word: "TINTENHERZ", hint: "Ein berühmtes Buch von Cornelia Funke über Figuren, die aus den Seiten zum Leben erweckt werden." },
    { word: "HEIDI", hint: "Ein Waisenmädchen lebt glücklich mit ihrem Großvater in den Schweizer Bergen und hütet Ziegen." },
    { word: "MAX UND MORITZ", hint: "Zwei Lausbuben aus einer alten Bildergeschichte von Wilhelm Busch, die den Erwachsenen Streiche spielen." },
    { word: "KÄPTN BLAUBÄR", hint: "Ein Seemann mit blauem Fell erzählt seinen Enkeln unglaubliche Lügengeschichten auf einem Schiff." },
    { word: "HEIN BLÖD", hint: "Eine gelbe, etwas tollpatschige Figur, die dem alten blauen Bären auf dem Schiff hilft." },
    { word: "DER KLEINE VAMPIR", hint: "Rüdiger hat spitze Zähne, kann fliegen, trinkt aber nur Milch und ist der beste Freund eines Menschenjungen." },
    { word: "LAURA", hint: "Ein kleines Mädchen findet eines Nachts ein verletztes, leuchtendes Himmelsobjekt und klebt ein Pflaster darauf." },
    { word: "STERN", hint: "Ein leuchtender Himmelskörper, dem ein kleines Mädchen ein Pflaster auf eine abgebrochene Zacke klebt." },
    { word: "KLEINER RABE SOCKE", hint: "Ein frecher, schwarzer Vogel mit einer rot-weiß gestreiften Kleidung am linken Fuß." },
    { word: "DER KLEINE KÖNIG", hint: "Ein kleiner Herr mit einer goldenen Krone auf dem Kopf lebt in einem Schloss mit seinem Pferd Grete." },
    { word: "RITTER ROST", hint: "Ein mutiger, aber oft tollpatschiger Blechmann auf einer Burg, der aus altem Metall gebaut ist." },
    { word: "MAJA", hint: "Ein kleines, gelb-schwarz gestreiftes Insekt verlässt seinen Stock, um Abenteuer auf der Blumenwiese zu erleben." },
    { word: "WILLI", hint: "Der beste, etwas dickere und sehr faule Freund der kleinen Biene, der am liebsten schläft und Honig frisst." },
    { word: "REGENBOGENFISCH", hint: "Ein Meeresbewohner mit glitzernden Schuppen, der lernt, seine Schönheit mit anderen zu teilen." },

    // ====== SCHULE & BILDUNG ======
    { word: "RANZEN", hint: "Eine große Tasche, die Kinder auf dem Rücken zur Schule tragen." },
    { word: "SCHULTÜTE", hint: "Ein großes, buntes Horn voller Süßigkeiten, das Kinder am ersten Schultag bekommen." },
    { word: "KLASSENZIMMER", hint: "Der Raum im Gebäude, in dem alle Tische stehen und die Kinder gemeinsam lernen." },
    { word: "LEHRER", hint: "Die Person, die vorne an der Tafel steht und den Kindern Lesen, Schreiben und Rechnen beibringt." },
    { word: "PAUSENHOF", hint: "Der Platz draußen vor dem Gebäude, auf dem Kinder zwischen den Stunden spielen und rennen können." },
    { word: "ZEUGNIS", hint: "Ein Papier am Ende des Schuljahres, auf dem steht, wie gut das Kind gelernt hat." },
    { word: "HAUSAUFGABEN", hint: "Übungen, die Kinder nach der Schule in ihrem eigenen Zimmer für den nächsten Tag machen müssen." },
    { word: "FEDERMAPPE", hint: "Eine kleine Tasche mit Reißverschluss, in der Stifte, Lineal und Radiergummi aufbewahrt werden." },
    { word: "LINEAL", hint: "Ein gerades Werkzeug aus Plastik oder Holz, mit dem man gerade Linien zeichnet und Zentimeter misst." },
    { word: "FÜLLER", hint: "Ein besonderer Stift, den ältere Grundschulkinder benutzen, der blaue Tinte aus Patronen braucht." },
    { word: "TINTE", hint: "Die blaue Flüssigkeit in einer Patrone, mit der Kinder in ihre Hefte schreiben." },
    { word: "FERIEN", hint: "Die schönste Zeit des Jahres, in der die Schule für mehrere Wochen geschlossen bleibt und alle entspannen." },

    // ====== KINDERMUSIK ======
    { word: "DEINE FREUNDE", hint: "Eine sehr bekannte deutsche Hip-Hop-Band für Familien, die coole Lieder über Schokolade und Schule singt." },
    { word: "ROLF ZUCKOWSKI", hint: "Ein berühmter Musiker, der Klassiker wie 'In der Weihnachtsbäckerei' für Familien geschrieben hat." },
    { word: "HEAVY SAURUS", hint: "Eine echte Rockband für Kinder, bei der alle Musiker wie große, grüne Urzeitechsen verkleidet sind." },
    { word: "VOLKER ROSIN", hint: "Ein bekannter Musiker, der viele fröhliche Lieder zum Mitmachen und Tanzen in der Minidisco singt." },
    { word: "DONIKKL", hint: "Die Band, die das berühmte 'Fliegerlied' erfunden hat, bei dem alle wie ein Flugzeug fliegen." },
    { word: "FLIEGERLIED", hint: "Ein super bekanntes Tanzlied, bei dem man wie ein Flugzeug fliegt, schwimmt und springt." },
    { word: "WIEGENLIED", hint: "Ein sehr ruhiges Musikstück, das Eltern ihren Babys am Bett vorsingen, damit sie einschlafen." },
    { word: "GITARRE", hint: "Ein Musikinstrument mit sechs Saiten, das oft im Musikunterricht oder am Lagerfeuer gespielt wird." },
    { word: "BLOCKFLÖTE", hint: "Ein kleines Blasinstrument aus Holz oder Plastik, das fast jedes Kind in der Grundschule lernt." },

    // ====== TIERE ======
    { word: "IGEL", hint: "Ein kleines Wildtier mit vielen spitzen Stacheln auf dem Rücken, das Winterschlaf hält." },
    { word: "FUCHS", hint: "Ein schlaues Waldtier mit rotem Fell und einem buschigen Schwanz." },
    { word: "REH", hint: "Ein scheues, braunes Waldtier mit großen Augen, oft mit weißen Punkten als Kitz." },
    { word: "MARIENKÄFER", hint: "Ein kleines, rotes Insekt mit schwarzen Punkten, das als Glücksbringer gilt." },
    { word: "PFERD", hint: "Ein großes Haustier, auf dem man reiten kann und das im Stall wohnt." },
    { word: "HUND", hint: "Der beste tierische Freund des Menschen, der gerne Stöckchen holt und laut bellt." },
    { word: "KATZE", hint: "Ein weiches Haustier, das gerne schnurrt, Milch trinkt und kleine Nagetiere jagt." },
    { word: "VOGEL", hint: "Ein Tier mit Federn und Flügeln, das hoch am Himmel fliegt und singt." },
    { word: "SCHMETTERLING", hint: "Ein wunderschönes Insekt mit bunten Flügeln, das früher eine Raupe war." },
    { word: "REGENWURM", hint: "Ein langes, rosa Tier ohne Beine, das in der feuchten Erde lebt." },

    // ====== SPIELZEUG & HOBBYS ======
    { word: "LEGO", hint: "Bunte Bausteine aus Plastik, die man zusammenstecken kann, um etwas zu bauen." },
    { word: "KREIDE", hint: "Bunte Stifte, mit denen Kinder Bilder auf die Straße oder die Tafel malen." },
    { word: "FUSSBALL", hint: "Ein runder Sportartikel, den zwei Mannschaften in ein Netz kicken wollen." },
    { word: "FAHRRAD", hint: "Ein Fahrzeug mit zwei Rädern und Pedalen, mit dem man im Park fährt." },
    { word: "SCHAUKEL", hint: "Ein Sitz auf dem Spielplatz, der an Ketten hängt und vor und zurück fliegt." },
    { word: "RUTSCHE", hint: "Ein langes Spielgerät aus Metall oder Plastik, auf dem man schnell nach unten gleitet." },
    { word: "PUPPE", hint: "Ein Spielzeug, das wie ein kleines Baby aussieht und im Wagen liegt." },
    { word: "ROLLER", hint: "Ein kleines Fahrzeug mit zwei Rollen und einem Lenker, auf das man sich mit einem Fuß stellt." },

    // ====== NATUR & SEASONS ======
    { word: "REGENBOGEN", hint: "Eine bunte Brücke am Himmel aus sieben Farben, die nach dem Schauer erscheint." },
    { word: "SONNE", hint: "Ein riesiger, heißer Stern am Himmel, der uns tagsüber wärmt und Licht bringt." },
    { word: "MOND", hint: "Eine große Kugel am Nachthimmel, die jede Nacht ihre Form verändert." },
    { word: "SCHNEE", hint: "Weiße, kalte Flocken, die im Winter vom Himmel fallen und aus denen man Figuren baut." },
    { word: "WALD", hint: "Ein großer Ort mit sehr vielen Bäumen, Pflanzen und wilden Tieren." },

    // ====== ESSEN & LECKEREIEN ======
    { word: "BREZEL", hint: "Ein typisch deutsches, braunes Gebäck mit Salz, das wie ein Knoten geformt ist." },
    { word: "APFEL", hint: "Eine runde Frucht, die knackig ist und rot, grün oder gelb sein kann." },
    { word: "ERDBEERE", hint: "Eine süße, rote Frucht im Sommer mit kleinen Nüssen auf der Haut." },
    { word: "EIS", hint: "Eine sehr kalte, süße Leckerei in der Waffel, die man im Sommer schleckt." },
    { word: "KUCHEN", hint: "Eine süße Speise aus dem Ofen, auf der oft Kerzen stehen." },

    // ====== FAHRZEUGE & BAUSTELLE ======
    { word: "BAGGER", hint: "Eine große Baumaschine mit einer riesigen Schaufel, die tiefe Löcher in die Erde gräbt." },
    { word: "TRAKTOR", hint: "Ein großes, laut brummendes Fahrzeug mit riesigen Hinterrädern, das der Bauer auf dem Feld benutzt." },
    { word: "FEUERWEHRAUTO", hint: "Ein großes rotes Fahrzeug mit einer Leiter auf dem Dach und einer lauten Sirene." },
    { word: "MÜLLAUTO", hint: "Ein großes Fahrzeug, das morgens durch die Straßen fährt und die Tonnen leert." },
    { word: "U-BAHN", hint: "Ein langer Zug, der tief unter der Erde fährt, um Menschen durch die Stadt zu bringen." },

    // ====== BERUFE ======
    { word: "TIERARZT", hint: "Ein medizinischer Helfer, der kranke Hunde, Katzen und andere Tiere wieder gesund macht." },
    { word: "PILOT", hint: "Eine Person, die ganz vorne in einem großen Flugzeug sitzt und es hoch durch die Wolken steuert." },
    { word: "BÄCKER", hint: "Ein Handwerker, der sehr früh morgens aufsteht, um frische Brötchen und Brot zu machen." },
    { word: "POLIZIST", hint: "Eine Person in Uniform, die auf den Straßen für Ordnung sorgt und Kindern hilft, den Weg zu finden." },
    { word: "ZAHNARZT", hint: "Ein Doktor, der kontrolliert, ob die Beißerchen der Kinder gesund und sauber sind." },

    // ====== FESTE & TRADITIONEN ======
    { word: "OSTERHASE", hint: "Ein löffelohriges Tier, das im Frühling bunte Eier im Garten für die Kinder versteckt." },
    { word: "WEIHNACHTSMANN", hint: "Ein alter Herr mit einem langen weißen Bart und einem roten Mantel, der im Winter Geschenke bringt." },
    { word: "GEBURTSTAG", hint: "Der schönste Tag im Jahr, an dem man Kerzen auspustet, Kuchen isst und Geschenke bekommt." },
    { word: "LATERNE", hint: "Ein buntes Licht aus Papier, das Kinder im Herbst bei einem großen Umzug durch die Straßen tragen." },

    // ====== FABELWESEN ======
    { word: "DRACHE", hint: "Ein großes, geflügeltes Wesen aus alten Geschichten, das feurige Luft aus dem Mund spucken kann." },
    { word: "EINHORN", hint: "Ein wunderschönes, weißes Pferd aus Fabelwelten mit einem magischen Auswuchs auf der Stirn." },
    { word: "MEERJUNGFRAU", hint: "Ein Wesen aus dem Ozean, das oben wie ein Mensch aussieht und unten einen glitzernden Fischschwanz hat." },

    // ====== KÖRPER & GEFÜHLE ======
    { word: "LACHEN", hint: "Das macht man mit dem Mund und zeigt allen, dass man gerade fröhlich und glücklich ist." },
    { word: "FREUNDSCHAFT", hint: "Wenn zwei Kinder sich super verstehen, alles miteinander teilen und immer zusammen spielen." },
    { word: "HERZ", hint: "Ein rotes Symbol für die Liebe, das auch tief in unserer Brust klopft." }
];
