# 🧭 WORKFLOW — Git + GitHub (fork + PR)

## 1. Rozdzielanie repozytorium (Fork + Clone + Remote)

1. Sklonuj repozytorium kursu:
```bash
git clone <repo_url>
```

2. Na GitHub wykonaj **Fork** repozytorium.

3. Sprawdź aktualne zdalne repozytoria:
```bash
git remote -v
```

**Wynik:**
```
origin  https://github.com/ed-donner/agents.git (fetch)
origin  https://github.com/ed-donner/agents.git (push)
```

4. Zmień nazwę `origin` → `upstream`:
```bash
git remote rename origin upstream
```

5. Dodaj swój fork jako `origin`:
```bash
git remote add origin https://github.com/<your-username>/agents.git
git remote -v
```

**Poprawny wynik:**
```
origin    https://github.com/<your-username>/agents.git (fetch)
origin    https://github.com/<your-username>/agents.git (push)
upstream  https://github.com/ed-donner/agents.git (fetch)
upstream  https://github.com/ed-donner/agents.git (push)
```

✅ Kontrola:
- `origin` → Twój fork (pushujesz tutaj)
- `upstream` → repo kursu (pullujesz stąd)

---

## 2. Przygotowanie wkładu (Branch + pliki)

1. Dodaj pliki do:
```
community_contributions/
```

2. Utwórz nową gałąź:
```bash
git checkout -b LandSur_PL/day1
```

---

## 3. Dodawanie i commit

1. Sprawdź status:
```bash
git status
```

2. Dodaj plik (zalecane):
```bash
git add section1/community_contributions/nazwa_mojego_pliku.ipynb
git status
```

lub wiele plików:
```bash
git add .\community_contributions\
```

3. Commit:
```bash
git commit -m "Add LandSur_PL's lab 1 solution (cleared outputs)"
git status
```

**Wynik:**
```
On branch LandSur_PL/day1
nothing to commit, working tree clean
```

4. Push:
```bash
git push -u origin LandSur_PL/day1
```

---

## 4. Pull Request (PR)

1. Na GitHub:
- kliknij **Compare & pull request**
lub
- Pull Requests → New Pull Request

2. Ustaw:
- base: `ed-donner/agents main`
- compare: `your-username/agents LandSur_PL/day1`

3. Kontrola:
- tylko zielone linie `+`
- ścieżka:
```
community_contributions/
```
- pliki <1MB
- ~<1000 linii

4. Uzupełnij:
- tytuł
- opis

5. Kliknij:
```
Create pull request
```

---

## 5. Synchronizacja fork

1. Aktualizacja:
```bash
git checkout main
git pull upstream main
git push origin main
```

2. Nowa praca:
```bash
git checkout -b LandSur_PL/nastepna_zmiana main
```


---




Jesteś pomocnikiem do tworzenia przejrzystych treści z moich notatek z dziedziny programowania.
W pliku przedstawiam treść którą ci przesyłam, która pochodzi z moich notatek z kursu ED-a Donera. Napisałem w swój sposób nie do końca dla mnie przejrzysty i prosty, opis kolejnych kroków w komend i przepływ pracy (workflow).
Twoim zadaniem jest z tego tekstu (notatek) stworzyć:
1. Workflow dla tego procesu, który będzie opisywał kolejne kroki - ten przepływ pracy będzie mi służył jako "ściąga" o wykonywania kolejnych kroków w codziennej pracy do czasu jak nie nauczę się tego przepływu.  
2. bazę wiedzy dotyczącej gita, z opisem tak abym mógł jeżeli czegoś nie zrozumiem albo zapomnę tą bazę wiedzy przejrzeć

Możesz: 
[ ] zmienić tekst jeżeli jest niepoprawny

Nie możesz:
[ ] zmieniać kolejności przepływu pracy
[ ] usuwać informacji o kontrolach i ich wynikach

Całość odpowiedzi wykonujesz w jednym formacie  markdown, tak abym mógł całą treść przesłać jednym kliknięciem do markdown dotyczy to punktów 1 i 2, jedna odpowiedź tylko mardown!

Jeżeli masz wątpliwości zadaj pytanie, przeprowadź recharge nie zmyślaj


Jasne — rozumiem dokładnie strukturę, jakiej oczekujesz (workflow + baza wiedzy w jednym dokumencie markdown, bez zmiany kolejności kroków i bez gubienia kontroli/walidacji).

Na ten moment brakuje jednak kluczowego elementu: Twoich notatek.

➡️ Prześlij proszę treść (plik lub wklej tekst), a wtedy:

uporządkuję workflow krok po kroku (czytelna „ściąga” operacyjna),

zbuduję równolegle bazę wiedzy (wyjaśnienia + kontekst do każdego kroku),

zachowam Twoją kolejność i wszystkie checkpointy/kontrole,

poprawię ewentualne błędy merytoryczne lub składniowe (bez zmiany logiki procesu).

Jeśli notatki są długie, możesz wysłać je w częściach — scalę je w jeden spójny dokument.



baza_wiedzy.ipynb
Plik
oto plik 

# 🧭 WORKFLOW — Git + GitHub (fork + PR)

## 1. Rozdzielanie repozytorium (Fork + Clone + Remote)

1. Sklonuj repozytorium kursu:
   ```bash
   git clone <repo_url>
Na GitHub wykonaj Fork repozytorium.

Sprawdź aktualne zdalne repozytoria:

git remote -v
Wynik:

origin  https://github.com/ed-donner/agents.git (fetch)
origin  https://github.com/ed-donner/agents.git (push)
Zmień nazwę origin → upstream:

git remote rename origin upstream
Dodaj swój fork jako origin:

git remote add origin https://github.com/<your-username>/agents.git
git remote -v
Poprawny wynik:

origin    https://github.com/<your-username>/agents.git (fetch)
origin    https://github.com/<your-username>/agents.git (push)
upstream  https://github.com/ed-donner/agents.git (fetch)
upstream  https://github.com/ed-donner/agents.git (push)
✅ Kontrola:

origin → Twój fork (tu wypychasz zmiany)

upstream → repo kursu (stąd pobierasz aktualizacje)

2. Przygotowanie wkładu (Branch + pliki)
Dodaj pliki do:

community_contributions/
Zawsze pracuj na nowej gałęzi:

git checkout -b LandSur_PL/day1
3. Dodawanie i zatwierdzanie zmian
Sprawdź status:

git status
Wynik:

pliki w Untracked lub Modified

Dodanie plików:

Pojedynczy plik (ZALECANE):

git add section1/community_contributions/nazwa_mojego_pliku.ipynb
git status
Wiele plików:

git add .\community_contributions\
Commit:

git commit -m "Add LandSur_PL's lab 1 solution (cleared outputs)"
git status
Wynik:

On branch LandSur_PL/day1 nothing to commit, working tree clean
Push:

git push -u origin LandSur_PL/day1
4. Pull Request (PR)
Na GitHub kliknij:

Compare & pull request

lub:

Pull Requests → New Pull Request

Ustaw:

base: ed-donner/agents main

compare: your-username/agents LandSur_PL/day1

Kontrola zmian:

tylko zielone linie +

ścieżka:

community_contributions/
pliki:

< 1MB

~<1000 linii

Uzupełnij:

tytuł

opis

Kliknij:

Create pull request
5. Synchronizacja fork (bardzo ważne 🔁)
Aktualizacja:

git checkout main
git pull upstream main
git push origin main
Nowa praca:

git checkout -b LandSur_PL/nastepna_zmiana main
Następnie:

pracuj

commit

push

PR

📚 BAZA WIEDZY — Git (zrozumienie procesu)
🔹 Remote: origin vs upstream
origin → Twój fork (Twoje repozytorium)

upstream → oryginalne repo kursu

👉 Model pracy:

upstream → (pull) → local → (push) → origin → PR → upstream
🔹 Fork vs Clone
Fork → kopia repo na GitHub (Twoja)

Clone → kopia repo na komputerze

👉 zawsze:

fork

clone

🔹 Branch (gałąź)
Branch = izolowane środowisko zmian

✔️ Dlaczego:

nie psujesz main

PR jest czysty

✔️ Nazewnictwo:

LandSur_PL/day1
🔹 git status (najważniejsza komenda)
Pokazuje:

co zmieniłeś

co jest staged

co nie jest

👉 używaj przed KAŻDYM krokiem

🔹 git add
Dodaje pliki do „staging area”

✔️ staging = przygotowanie do commit

✔️ dobre praktyki:

dodawaj konkretny plik (nie . jeśli nie musisz)

🔹 git commit
Tworzy zapis zmian

✔️ commit = snapshot projektu

✔️ komunikat:

co zrobiłeś

krótko i konkretnie

🔹 git push
Wysyła zmiany:

lokalny → GitHub (origin)
🔹 Pull Request (PR)
PR = prośba o dodanie zmian do głównego repo

✔️ zawiera:

diff (różnice)

opis

review

🔹 git pull upstream main
Pobiera zmiany z repo kursu i łączy z lokalnym

👉 zapobiega konfliktom

🔹 git push origin main
Synchronizuje Twój fork z lokalnym repo

⚠️ Błędy i rozwiązania
Problem	Przyczyna	Rozwiązanie
Pliki spoza community_contributions	Dodane przypadkowo	bash git restore --staged path/to/file git checkout -- path/to/file
Duże zmiany JSON w notebooku	Output nie wyczyszczony	Wyczyść output → zapisz → add → commit
non-fast-forward	Lokalna gałąź nieaktualna	bash git pull --rebase origin <branch>
remote origin already exists	origin już istnieje	bash git remote -v
Usunięty plik w PR	Commit usunął plik	Przywróć → add → commit → push
Duży plik w repo	Nie powinien być śledzony	bash git rm --cached path/to/file + .gitignore
🧠 KLUCZOWE ZASADY (skrót mentalny)
Zawsze pracuj na branchu

Zawsze sprawdzaj git status

Dodawaj tylko potrzebne pliki

Czyść notebooki przed commit

Sync z upstream regularnie

PR = tylko Twoje zmiany


treść nie jest jednolita w markdown muszę wykonywać kilkudziesięciu kopiuj i wklej popraw

Poniżej masz jednolity, czysty blok Markdown — bez rozbicia, bez dodatkowych znaczników, gotowy do jednego kopiuj-wklej:

# 🧭 WORKFLOW — Git + GitHub (fork + PR)

## 1. Rozdzielanie repozytorium (Fork + Clone + Remote)

1. Sklonuj repozytorium kursu:
```bash
git clone <repo_url>
```

2. Na GitHub wykonaj **Fork** repozytorium.

3. Sprawdź aktualne zdalne repozytoria:
```bash
git remote -v
```

**Wynik:**
```
origin  https://github.com/ed-donner/agents.git (fetch)
origin  https://github.com/ed-donner/agents.git (push)
```

4. Zmień nazwę `origin` → `upstream`:
```bash
git remote rename origin upstream
```

5. Dodaj swój fork jako `origin`:
```bash
git remote add origin https://github.com/<your-username>/agents.git
git remote -v
```

**Poprawny wynik:**
```
origin    https://github.com/<your-username>/agents.git (fetch)
origin    https://github.com/<your-username>/agents.git (push)
upstream  https://github.com/ed-donner/agents.git (fetch)
upstream  https://github.com/ed-donner/agents.git (push)
```

✅ Kontrola:
- `origin` → Twój fork (pushujesz tutaj)
- `upstream` → repo kursu (pullujesz stąd)

---

## 2. Przygotowanie wkładu (Branch + pliki)

1. Dodaj pliki do:
```
community_contributions/
```

2. Utwórz nową gałąź:
```bash
git checkout -b LandSur_PL/day1
```

---

## 3. Dodawanie i commit

1. Sprawdź status:
```bash
git status
```

2. Dodaj plik (zalecane):
```bash
git add section1/community_contributions/nazwa_mojego_pliku.ipynb
git status
```

lub wiele plików:
```bash
git add .\community_contributions\
```

3. Commit:
```bash
git commit -m "Add LandSur_PL's lab 1 solution (cleared outputs)"
git status
```

**Wynik:**
```
On branch LandSur_PL/day1
nothing to commit, working tree clean
```

4. Push:
```bash
git push -u origin LandSur_PL/day1
```

---

## 4. Pull Request (PR)

1. Na GitHub:
- kliknij **Compare & pull request**
lub
- Pull Requests → New Pull Request

2. Ustaw:
- base: `ed-donner/agents main`
- compare: `your-username/agents LandSur_PL/day1`

3. Kontrola:
- tylko zielone linie `+`
- ścieżka:
```
community_contributions/
```
- pliki <1MB
- ~<1000 linii

4. Uzupełnij:
- tytuł
- opis

5. Kliknij:
```
Create pull request
```

---

## 5. Synchronizacja fork

1. Aktualizacja:
```bash
git checkout main
git pull upstream main
git push origin main
```

2. Nowa praca:
```bash
git checkout -b LandSur_PL/nastepna_zmiana main
```

---

# 📚 BAZA WIEDZY — Git

## Remote: origin vs upstream

- **origin** → Twój fork
- **upstream** → repo kursu

Model:
```
upstream → pull → lokalne → push → origin → PR → upstream
```

---

## Fork vs Clone

- Fork → kopia na GitHub
- Clone → kopia lokalna

Kolejność:
1. fork
2. clone

---

## Branch

Branch = izolacja zmian

Dlaczego:
- nie psujesz main
- PR jest czysty

Nazewnictwo:
```
LandSur_PL/day1
```

---

## git status

Pokazuje:
- zmiany
- staged
- niestaged

👉 używaj często

---

## git add

Dodaje do staging

- staging = przygotowanie do commit
- lepiej dodawać konkretne pliki

---

## git commit

Snapshot zmian

- krótki opis
- co zostało zrobione

---

## git push

Wysyła zmiany:
```
lokalnie → GitHub (origin)
```

---

## Pull Request

PR = prośba o dodanie zmian

Zawiera:
- diff
- opis
- review

---

## git pull upstream main

Pobiera aktualizacje z repo kursu

---

## git push origin main

Synchronizuje fork

---

# ⚠️ Błędy i rozwiązania

| Problem | Przyczyna | Rozwiązanie |
|--------|----------|------------|
| Złe pliki | dodane za dużo | `git restore --staged path` |
| Duże JSON | output notebooka | wyczyść output |
| non-fast-forward | brak aktualizacji | `git pull --rebase origin <branch>` |
| origin exists | już istnieje | `git remote -v` |
| usunięty plik | commit usunął | przywróć + commit |
| duży plik | nie powinien być w repo | `git rm --cached file` + `.gitignore` |

---

# 🧠 Zasady

- zawsze branch
- zawsze `git status`
- dodawaj tylko potrzebne pliki
- czyść notebooki
- synchronizuj z upstream
- PR = tylko Twoje zmiany


---  


# 🧭 SCHEMAT — Workflow Git + GitHub (Fork + PR)

---

| Przepływ | Komendy / co się dzieje |
|----------|------------------------|
| **Start (klon + fork)** | `git clone <repo_url>` <br> wykonujesz **Fork** na GitHub |
| ↓ | pobierasz repo lokalnie <br> tworzysz własną kopię na GitHub |
| **Sprawdzenie remote** | `git remote -v` |
| ↓ | widzisz `origin` wskazujący na repo kursu |
| **Zmiana konfiguracji remote** | `git remote rename origin upstream` <br> `git remote add origin https://github.com/<user>/repo.git` <br> `git remote -v` |
| ↓ | `upstream` = repo kursu <br> `origin` = Twój fork |
| **Kontrola remote (KLUCZOWE)** | sprawdzasz czy: <br> `origin` → Twój fork <br> `upstream` → repo kursu |
| ↓ | jeśli błąd → wróć do konfiguracji remote |
| **Tworzenie branch** | `git checkout -b LandSur_PL/day1` |
| ↓ | tworzysz i przełączasz się na nową gałąź |
| **Dodanie plików** | dodajesz pliki do: <br> `community_contributions/` |
| ↓ | przygotowujesz wkład do repo |
| **Sprawdzenie statusu** | `git status` |
| ↓ | widzisz zmodyfikowane / nowe pliki |
| **Dodanie do staging** | `git add section1/community_contributions/plik.ipynb` <br> *(lub)* `git add .\community_contributions\` |
| ↓ | dodajesz pliki do commit |
| **Kontrola przed commit** | `git status` |
| ↓ | upewniasz się co zostanie zapisane |
| **Commit zmian** | `git commit -m "opis zmiany"` |
| ↓ | tworzysz snapshot projektu |
| **Kontrola po commit** | `git status` |
| ↓ | oczekiwany wynik: `working tree clean` |
| **Push do GitHub** | `git push -u origin LandSur_PL/day1` |
| ↓ | wysyłasz branch do swojego repo (`origin`) |
| **Pull Request (PR)** | GitHub: **Compare & pull request** |
| ↓ | tworzysz propozycję zmian |
| **Kontrola PR (KLUCZOWE)** | sprawdzasz: <br> tylko `community_contributions/` <br> tylko zielone `+` <br> pliki <1MB |
| ↓ | jeśli błąd → wróć do `git add / commit` |
| **Tworzenie PR** | klikasz `Create pull request` |
| ↓ | zmiany trafiają do review |
| **Synchronizacja fork** | `git checkout main` <br> `git pull upstream main` <br> `git push origin main` |
| ↓ | aktualizujesz lokalne repo i fork |
| **Nowa praca** | `git checkout -b LandSur_PL/nastepna_zmiana main` |
| ↓ | zaczynasz kolejny cykl pracy |
| **LOOP 🔁** | wracasz do: `git status` |
| ↓ | powtarzasz proces dla kolejnych zmian |

---

# 🔁 MODEL PRZEPŁYWU (skrót)

| Etap | Przepływ |
|------|---------|
| Synchronizacja | `upstream → lokalne` |
| Praca | `lokalne → commit` |
| Publikacja | `lokalne → origin` |
| Integracja | `origin → PR → upstream` |

---

# ⚠️ KLUCZOWE KONTROLE

| Moment | Co sprawdzasz | Oczekiwany wynik |
|-------|--------------|------------------|
| remote | `git remote -v` | origin = fork, upstream = kurs |
| przed commit | `git status` | właściwe pliki |
| po commit | `git status` | working tree clean |
| PR | diff | tylko Twoje zmiany |

---

# 🧠 MINIMALNY SKRÓT (1 linia)

| Krok |
|------|
| clone → fork → remote → branch → add → commit → push → PR → sync → repeat |

