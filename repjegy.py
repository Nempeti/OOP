import json                          # JSON formátumú fájlkezeléshez
from abc import ABC, abstractmethod # Absztrakt osztályok és metódusok definiálásához
from datetime import datetime       # Dátumkezeléshez
import os                           # Fájl- és elérési út ellenőrzéshez


# Absztrakt Jarat osztály – ez az alapja minden járat típusnak
class Jarat(ABC):
    def __init__(self, jaratszam, celallomas, jegyar):
        self.jaratszam = jaratszam
        self.celallomas = celallomas
        self.jegyar = jegyar

    @abstractmethod
    def jarat_tipus(self):          # Kötelezően implementálandó metódus
        pass

    @abstractmethod
    def get_jegy_ar(self):         # Jegy árának kiszámítását végző metódus
        pass

    def __str__(self):             # Objektum szöveges megjelenítése
        return f"{self.jaratszam:<6} | {self.celallomas:<15} | {self.jarat_tipus():<12} | {self.get_jegy_ar():>7} Ft"


# Belföldi járat osztály – a Jarat egy implementációja
class BelfoldiJarat(Jarat):
    def jarat_tipus(self):
        return "Belföldi"

    def get_jegy_ar(self):
        return int(self.jegyar * 0.9)  # 10% kedvezmény


# Nemzetközi járat osztály
class NemzetkoziJarat(Jarat):
    def jarat_tipus(self):
        return "Nemzetközi"

    def get_jegy_ar(self):
        return int(self.jegyar * 1.2)  # 20% felár


# Foglalásokat leíró osztály
class JegyFoglalas:
    def __init__(self, foglalas_id, utas_nev, jarat, datum):
        self.foglalas_id = foglalas_id
        self.utas_nev = utas_nev
        self.jarat = jarat
        self.datum = datum

    def __str__(self):
        return f"{self.foglalas_id:03d} | {self.utas_nev:<20} | {self.jarat.jaratszam:<6} | {self.jarat.celallomas:<15} | {self.datum.strftime('%Y-%m-%d')}"

    def to_dict(self):  # Segédfüggvény JSON mentéshez
        return {
            "foglalas_id": self.foglalas_id,
            "utas_nev": self.utas_nev,
            "jaratszam": self.jarat.jaratszam,
            "datum": self.datum.strftime("%Y-%m-%d")
        }


# Légitársaság – a foglalási logikát és járatokat kezeli
class LegiTarsasag:
    def __init__(self, nev):
        self.nev = nev
        self.jaratok = []
        self.foglalasok = {}
        self.kov_foglalas_id = 1

    def jarat_hozzaadas(self, jarat):
        self.jaratok.append(jarat)  # Járat hozzáadása

    def jaratok_listazasa(self):   # Járatok szépen formázott listája
        fejl = f"{'Sorsz.':<6} | {'Járatszám':<6} | {'Célállomás':<15} | {'Típus':<12} | {'Jegyár':>7}"
        vonal = "-" * len(fejl)
        sorok = [f"{idx+1:<6} | {str(jarat)}" for idx, jarat in enumerate(self.jaratok)]
        return f"{fejl}\n{vonal}\n" + "\n".join(sorok)

    def get_jarat_by_index(self, index):
        return self.jaratok[index] if 0 <= index < len(self.jaratok) else None

    def get_jarat_by_szam(self, jaratszam):  # Járat lekérdezése járatszám alapján
        return next((j for j in self.jaratok if j.jaratszam == jaratszam), None)

    def jegy_foglalas(self, utas_nev, jarat_index, datum):
        try:
            datum = datetime.strptime(datum, "%Y-%m-%d")
            if datum < datetime.now():
                return "A dátum nem lehet múltbéli."  # Csak jövőbeli dátum engedélyezett
        except ValueError:
            return "Érvénytelen dátum formátum."       # Hibás dátum formátum

        jarat = self.get_jarat_by_index(jarat_index)
        if jarat:
            foglalas_id = self.kov_foglalas_id
            foglalas = JegyFoglalas(foglalas_id, utas_nev, jarat, datum)
            self.foglalasok[foglalas_id] = foglalas
            self.kov_foglalas_id += 1
            return f"Foglalás sikeres! Ár: {jarat.get_jegy_ar()} Ft. Foglalás ID: {foglalas_id}"
        return "Érvénytelen járatválasztás."

    def foglalas_lemondas(self, foglalas_id):  # Foglalás törlése ID alapján
        if foglalas_id in self.foglalasok:
            del self.foglalasok[foglalas_id]
            return "Foglalás lemondva."
        return "Nem létező foglalás."

    def foglalasok_listazasa(self):  # Foglalások listázása
        if not self.foglalasok:
            return "Nincsenek foglalások."
        fejl = f"{'ID':<3} | {'Utas neve':<20} | {'Járat':<6} | {'Célállomás':<15} | {'Dátum'}"
        vonal = "-" * len(fejl)
        sorok = [str(f) for f in self.foglalasok.values()]
        return f"{fejl}\n{vonal}\n" + "\n".join(sorok)

    def mentes_fajlba(self, fajlnev="foglalasok.json"):  # Mentés JSON fájlba
        adatok = [f.to_dict() for f in self.foglalasok.values()]
        with open(fajlnev, "w", encoding="utf-8") as f:
            json.dump(adatok, f, ensure_ascii=False, indent=4)

    def betoltes_fajlbol(self, fajlnev="foglalasok.json"):  # Betöltés fájlból
        if not os.path.exists(fajlnev):
            return
        with open(fajlnev, "r", encoding="utf-8") as f:
            adatok = json.load(f)
            for adat in adatok:
                jarat = self.get_jarat_by_szam(adat["jaratszam"])
                if jarat:
                    datum = datetime.strptime(adat["datum"], "%Y-%m-%d")
                    foglalas = JegyFoglalas(adat["foglalas_id"], adat["utas_nev"], jarat, datum)
                    self.foglalasok[adat["foglalas_id"]] = foglalas
                    self.kov_foglalas_id = max(self.kov_foglalas_id, adat["foglalas_id"] + 1)


# Példányosítunk egy légitársaságot, és hozzáadunk járatokat
legi_tarsasag = LegiTarsasag("Peti Air - A széllel szállunk")
legi_tarsasag.jarat_hozzaadas(BelfoldiJarat("B101", "Budapest", 15000))
legi_tarsasag.jarat_hozzaadas(NemzetkoziJarat("N202", "London", 55000))
legi_tarsasag.jarat_hozzaadas(NemzetkoziJarat("N303", "New York", 120000))
legi_tarsasag.betoltes_fajlbol()


# Menü logika – konzolos felhasználói felület
def menu():
    print("""
        (díszített cím blokk – design elem)
""")
    while True:
        print("""
Menü opciók:
1. Jegy foglalása
2. Foglalás lemondása
3. Foglalások listázása
4. Kilépés
""")
        valasztas = input("Válassz egy opciót (1-4): ")

        if valasztas == "1":
            nev = input("Utas neve: ")
            print("Elérhető járatok:\n")
            print(legi_tarsasag.jaratok_listazasa())
            try:
                index = int(input("\nVálaszd ki a járat sorszámát: ")) - 1
                datum = input("Dátum (ÉÉÉÉ-HH-NN): ")
                print("\n" + legi_tarsasag.jegy_foglalas(nev, index, datum))
            except ValueError:
                print("Hibás járat index.")
        elif valasztas == "2":
            try:
                foglalas_id = int(input("Foglalás ID: "))
                print("\n" + legi_tarsasag.foglalas_lemondas(foglalas_id))
            except ValueError:
                print("Hibás ID.")
        elif valasztas == "3":
            print("Aktuális foglalások:\n")
            print(legi_tarsasag.foglalasok_listazasa())
        elif valasztas == "4":
            print("\nMentés folyamatban...")
            legi_tarsasag.mentes_fajlba()
            print("Kilépés...")
            break
        else:
            print("Érvénytelen opció.")


# A program belépési pontja
if __name__ == "__main__":
    menu()
