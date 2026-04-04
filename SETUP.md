# Vehicule — Ghid de instalare și configurare

Integrare Home Assistant pentru gestionarea vehiculelor: documente, asigurări, taxe, mentenanță, costuri și istoric — totul local, fără API-uri externe.

**Depozitul oficial:** https://github.com/cnecrea/vehicule

---

## Ghid video de instalare

Pentru o demonstrație completă a procesului de instalare și configurare, urmăriți tutorialul video:

[![Tutorial instalare Vehicule](https://img.youtube.com/vi/vCtOu52y5bM/maxresdefault.jpg)](https://www.youtube.com/watch?v=vCtOu52y5bM)

---

## Cerințe

- Home Assistant **2025.11.0** sau mai nou
- **HACS** (opțional, pentru instalare simplificată)
- **Licență** validă — de la [hubinteligent.org/donate?ref=vehicule](https://hubinteligent.org/donate?ref=vehicule)
- Acces administrativ în Home Assistant
- Nu este necesară conexiunea la internet — integrarea funcționează 100% local

---

## Instalare

### Metoda 1: Prin HACS (recomandată)

1. Deschideți **HACS** în Home Assistant
2. Click pe cele 3 puncte (⋮) → **Custom repositories**
3. Adăugați:
   - **URL:** `https://github.com/cnecrea/vehicule`
   - **Categorie:** Integration
4. Căutați **„Vehicule"** → **Install**
5. Reporniți Home Assistant

### Metoda 2: Manual

1. Descărcați ultimul release de la: https://github.com/cnecrea/vehicule/releases
2. Copiați folderul `vehicule` în `config/custom_components/`
3. Calea finală: `<HA_CONFIG_DIR>/custom_components/vehicule/`
4. Reporniți Home Assistant

---

## Configurare inițială

1. **Setări** → **Dispozitive și servicii** → **Adaugă integrare**
2. Căutați **„Vehicule"**
3. Introduceți numărul de înmatriculare, fără spații (ex: `B123ABC`)
4. Click **Salvare**

Integrarea creează un dispozitiv cu un singur senzor (Informații). Restul senzorilor apar pe măsură ce completați date.

---

## Licență

Integrarea necesită o **licență validă** pentru a funcționa. Fără licență:
- Se creează doar senzorul `sensor.vehicule_{nr_normalizat}_licenta` cu valoarea „Licență necesară"
- Toți senzorii normali sunt dezactivați

Pentru a introduce licența:
1. **Setări** → **Dispozitive și Servicii**
2. Găsești **Vehicule** → click pe **Configurare**
3. Selectează **Licență**
4. Introdu cheia de licență
5. Click **Salvează**

Licențe disponibile la: [hubinteligent.org/donate?ref=vehicule](https://hubinteligent.org/donate?ref=vehicule)

---

## Editarea datelor vehiculului

1. **Setări** → **Dispozitive și servicii** → click pe intrarea vehiculului
2. Click **Configurare** (⚙️)
3. Alegeți categoria dorită din meniu:

```
Gestionare vehicul
├── Date de identificare
├── Asigurare RCA
├── Asigurare Casco
├── Inspecție tehnică (ITP)
├── Rovinieta
├── Date administrative / fiscale
├── Mentenanță
│   ├── Revizie ulei
│   ├── Distribuție
│   ├── Anvelope
│   ├── Baterie
│   ├── Frâne (plăcuțe și discuri)
│   ├── Trusă de prim ajutor
│   └── Extinctor
└── Actualizare kilometraj
```

### Câmpurile pe categorii

#### Date de identificare

| Câmp | Descriere | Exemplu |
|------|-----------|---------|
| Marcă | Producătorul vehiculului | Dacia |
| Model | Modelul vehiculului | Duster |
| An fabricație | An pe 4 cifre | 2018 |
| An prima înmatriculare | An pe 4 cifre | 2019 |
| Serie CIV | Seria certificatului de înmatriculare | K012345 |
| VIN | Identificatorul unic al vehiculului | WVWZZZ... |
| Motorizare | Tipul motorului | 1.5 dCi |
| Combustibil | Selectare din: benzină, diesel, hybrid, electric, GPL | diesel |
| Capacitate cilindrică (cm³) | Capacitatea motorului | 1461 |
| Putere (kW) | Puterea în kilowați | 81 |
| Putere (CP) | Puterea în cai putere | 110 |

#### Asigurare RCA

| Câmp | Descriere |
|------|-----------|
| Număr poliță | Numărul poliței de asigurare |
| Companie | Compania de asigurări |
| Data emitere | Data emiterii poliței (ZZ.LL.AAAA) |
| Data expirare | Data expirării poliței (ZZ.LL.AAAA) |
| Cost (RON) | Costul poliței |

#### Asigurare Casco

Aceleași câmpuri ca la RCA (Număr poliță, Companie, Data emitere, Data expirare, Cost).

#### ITP (Inspecție tehnică periodică)

| Câmp | Descriere |
|------|-----------|
| Data expirare | Data expirării ITP (ZZ.LL.AAAA) |
| Stație | Stația unde s-a efectuat ITP |
| Kilometraj la ITP | Km la momentul inspecției |

> **Notă:** Necesită setarea prealabilă a kilometrajului curent.

#### Rovinieta

| Câmp | Descriere |
|------|-----------|
| Data început | Data de la care este valabilă (ZZ.LL.AAAA) |
| Data sfârșit | Data până la care este valabilă (ZZ.LL.AAAA) |
| Categorie | Categoria rovinietei |
| Preț (RON) | Costul rovinietei |

#### Date administrative / fiscale

| Câmp | Descriere |
|------|-----------|
| Impozit — Sumă (RON) | Valoarea impozitului auto |
| Impozit — Scadență | Data scadenței (ZZ.LL.AAAA) |
| Impozit — Localitate | Localitatea impozitării |
| Proprietar | Numele proprietarului |
| Tip proprietate | Proprietate sau Leasing |
| Leasing — Data expirare | Apare doar dacă tipul e „Leasing" (ZZ.LL.AAAA) |

#### Mentenanță — Revizie ulei

| Câmp | Descriere |
|------|-----------|
| Km ultima revizie | Kilometrajul la ultima revizie |
| Km următoarea revizie | Kilometrajul la care trebuie făcută următoarea |
| Data ultima revizie | Data ultimei revizii (ZZ.LL.AAAA) |
| Cost (RON) | Costul reviziei |

> **Notă:** Necesită setarea prealabilă a kilometrajului curent.

#### Mentenanță — Distribuție

| Câmp | Descriere |
|------|-----------|
| Km ultima schimbare | Kilometrajul la ultima schimbare |
| Km următoarea schimbare | Kilometrajul la care trebuie schimbat |
| Data ultima schimbare | Data ultimei schimbări (ZZ.LL.AAAA) |
| Cost (RON) | Costul schimbării |

> **Notă:** Necesită setarea prealabilă a kilometrajului curent.

#### Mentenanță — Anvelope

| Câmp | Descriere |
|------|-----------|
| Data montare vară | Data montării anvelopelor de vară (ZZ.LL.AAAA) |
| Data montare iarnă | Data montării anvelopelor de iarnă (ZZ.LL.AAAA) |
| Cost (RON) | Costul anvelopelor |

#### Mentenanță — Baterie

| Câmp | Descriere |
|------|-----------|
| Data schimb | Data schimbării bateriei (ZZ.LL.AAAA) |
| Cost (RON) | Costul bateriei |

#### Mentenanță — Frâne (plăcuțe și discuri)

| Câmp | Descriere |
|------|-----------|
| Plăcuțe — Km ultima schimbare | Kilometrajul la ultima schimbare |
| Plăcuțe — Km următoarea schimbare | Kilometrajul la care trebuie schimbate |
| Plăcuțe — Data schimbare | Data schimbării plăcuțelor (ZZ.LL.AAAA) |
| Plăcuțe — Cost (RON) | Costul plăcuțelor |
| Discuri — Km ultima schimbare | Kilometrajul la ultima schimbare |
| Discuri — Km următoarea schimbare | Kilometrajul la care trebuie schimbate |
| Discuri — Data schimbare | Data schimbării discurilor (ZZ.LL.AAAA) |
| Discuri — Cost (RON) | Costul discurilor |

> **Notă:** Necesită setarea prealabilă a kilometrajului curent.

#### Echipament obligatoriu — Trusă de prim ajutor

| Câmp | Descriere |
|------|-----------|
| Data expirare | Data expirării trusei (ZZ.LL.AAAA) |

#### Echipament obligatoriu — Extinctor

| Câmp | Descriere |
|------|-----------|
| Data expirare | Data expirării extinctorului (ZZ.LL.AAAA) |

#### Actualizare kilometraj

| Câmp | Descriere |
|------|-----------|
| Km curent | Kilometrajul actual al vehiculului |

### Arhivare date (istoric)

Fiecare formular arhivabil (RCA, Casco, ITP, Rovinieta, Revizie ulei, Distribuție, Anvelope, Baterie, Frâne) conține un toggle **„Arhivează datele vechi înainte de salvare"** (implicit dezactivat).

- **Bifat**: datele vechi sunt salvate în istoric înainte de suprascriere (util la reînnoire)
- **Nebifat**: se salvează direct, fără arhivare (util pentru corecții)

Istoricul apare direct pe senzorul categoriei respective, cu prefix „Anterior –".

### Format date

Toate datele calendaristice se introduc în format **ZZ.LL.AAAA** (ex: 18.04.2026). Intern, se stochează în format ISO (2026-04-18).

---

## Senzori creați

Pentru fiecare vehicul, integrarea creează până la **17 senzori**. Aceștia apar condiționat — doar dacă au date completate.

Entity ID-uri: `sensor.vehicule_{nr_normalizat}_{tip_senzor}` (ex: `sensor.vehicule_b123abc_rca`)

| Senzor | Cheie | Unitate | Vizibil când... | Valoare |
|--------|-------|---------|-----------------|---------|
| Informații | `informatii` | — | Mereu | Marcă + Model |
| Kilometraj | `kilometraj` | km | `km_curent` completat | Km curent |
| RCA | `rca` | zile | `rca_data_expirare` completat | Zile rămase |
| Casco | `casco` | zile | `casco_data_expirare` completat | Zile rămase |
| ITP | `itp` | zile | `itp_data_expirare` completat | Zile rămase |
| Rovinieta | `rovinieta` | zile | `rovinieta_data_sfarsit` completat | Zile rămase |
| Impozit | `impozit` | zile | `impozit_scadenta` completat | Zile rămase |
| Leasing | `leasing` | zile | `tip_proprietate` = leasing | Zile rămase |
| Revizie ulei | `revizie_ulei` | km | `revizie_ulei_km_urmator` completat | Km rămași |
| Distribuție | `distributie` | km | `distributie_km_urmator` completat | Km rămași |
| Anvelope | `anvelope` | — | Cel puțin o dată de montare | Sezon (Vară / Iarnă) |
| Baterie | `baterie` | luni | `baterie_data_schimb` completat | Luni de la schimb |
| Plăcuțe frână | `placute_frana` | km | `placute_frana_km_urmator` completat | Km rămași |
| Discuri frână | `discuri_frana` | km | `discuri_frana_km_urmator` completat | Km rămași |
| Trusă prim ajutor | `trusa_prim_ajutor` | zile | `trusa_prim_ajutor_data_expirare` completat | Zile rămase |
| Extinctor | `extinctor` | zile | `extinctor_data_expirare` completat | Zile rămase |
| Cost total | `cost_total` | RON | Cel puțin un cost completat | Costul anului curent |

### Atribute senzori

Fiecare senzor expune atribute suplimentare. Exemple:

**RCA** — Număr poliță, Companie, Data emitere, Data expirare, Cost (RON), Stare (Valid/Expirat)

**Revizie ulei** — Km ultima revizie, Km următoarea revizie, Data ultima revizie, Cost (RON), Km curent

**Frâne (plăcuțe/discuri)** — Km ultima schimbare, Km următoarea schimbare, Data schimbare, Cost (RON), Km curent

**Cost total** — Asigurări {an} (RON), Taxe {an} (RON), Mentenanță {an} (RON), Total {an-1} (RON), Total general (RON). Fiecare cost e atribuit anului din data sa de referință. Totalurile per an includ și costurile arhivate.

**Istoric per senzor** — Senzorii arhivabili afișează: Reînnoiri anterioare, Ultima arhivare, câmpurile anterioare cu prefix „Anterior –", Cost total anterior (RON).

---

## Servicii

### vehicule.actualizeaza_date

Actualizează kilometrajul curent al unui vehicul.

| Parametru | Tip | Obligatoriu | Descriere | Exemplu |
|-----------|-----|-------------|-----------|---------|
| `nr_inmatriculare` | string | Da | Placa vehiculului | `B123ABC` |
| `km_curent` | int | Da | Kilometrajul actual (0–9.999.999) | `85000` |

```yaml
action: vehicule.actualizeaza_date
data:
  nr_inmatriculare: "B123ABC"
  km_curent: 85000
```

### vehicule.exporta_date

Exportă datele unui vehicul într-un fișier JSON în `/config/`.

| Parametru | Tip | Obligatoriu | Descriere |
|-----------|-----|-------------|-----------|
| `nr_inmatriculare` | string | Da | Placa vehiculului |

```yaml
action: vehicule.exporta_date
data:
  nr_inmatriculare: "B123ABC"
```

Fișierul generat: `/config/vehicule_backup_b123abc.json`

### vehicule.importa_date

Importă datele unui vehicul dintr-un fișier JSON. Dacă vehiculul nu există, va fi creat automat.

| Parametru | Tip | Obligatoriu | Descriere |
|-----------|-----|-------------|-----------|
| `cale_fisier` | string | Da | Calea completă către fișierul JSON |

```yaml
action: vehicule.importa_date
data:
  cale_fisier: "/config/vehicule_backup_b123abc.json"
```

### vehicule.actualizeaza_rovinieta

Actualizează datele rovinietei pentru un vehicul identificat prin numărul de înmatriculare. Datele calendaristice pot fi în format ISO (`2026-03-12`), ISO cu timp (`2026-03-12 09:52:47`) sau românesc (`12.03.2026`).

| Parametru | Tip | Obligatoriu | Descriere | Exemplu |
|-----------|-----|-------------|-----------|---------|
| `nr_inmatriculare` | string | Da | Placa vehiculului | `B123ABC` |
| `data_inceput` | string | Nu | Data de început valabilitate | `2026-03-12` |
| `data_sfarsit` | string | Nu | Data de sfârșit valabilitate | `2027-03-11` |
| `categorie` | string | Nu | Categoria rovinietei | `A` |
| `pret` | float | Nu | Prețul în RON (0–99.999) | `28` |
| `arhivare` | bool | Nu | Arhivează datele vechi (implicit: `false`) | `true` |

```yaml
action: vehicule.actualizeaza_rovinieta
data:
  nr_inmatriculare: "B123ABC"
  data_inceput: "2026-03-12"
  data_sfarsit: "2027-03-11"
  categorie: "A"
  pret: 28
  arhivare: true
```

### vehicule.actualizeaza_itp

Actualizează datele ITP pentru un vehicul.

| Parametru | Tip | Obligatoriu | Descriere | Exemplu |
|-----------|-----|-------------|-----------|---------|
| `nr_inmatriculare` | string | Da | Placa vehiculului | `B123ABC` |
| `data_expirare` | string | Nu | Data de expirare ITP | `2027-04-15` |
| `statie` | string | Nu | Stația ITP | `ITP Auto Service SRL` |
| `kilometraj` | int | Nu | Km la momentul inspecției (0–9.999.999) | `85000` |
| `arhivare` | bool | Nu | Arhivează datele vechi (implicit: `false`) | `true` |

```yaml
action: vehicule.actualizeaza_itp
data:
  nr_inmatriculare: "B123ABC"
  data_expirare: "2027-04-15"
  statie: "ITP Auto Service SRL"
  kilometraj: 85000
  arhivare: true
```

### vehicule.actualizeaza_rca

Actualizează datele asigurării RCA pentru un vehicul.

| Parametru | Tip | Obligatoriu | Descriere | Exemplu |
|-----------|-----|-------------|-----------|---------|
| `nr_inmatriculare` | string | Da | Placa vehiculului | `B123ABC` |
| `numar_polita` | string | Nu | Numărul poliței | `RCA-2026-123456` |
| `companie` | string | Nu | Compania de asigurare | `Euroins` |
| `data_emitere` | string | Nu | Data emiterii | `2026-04-01` |
| `data_expirare` | string | Nu | Data expirării | `2027-04-01` |
| `cost` | float | Nu | Cost în RON (0–99.999) | `1500` |
| `arhivare` | bool | Nu | Arhivează datele vechi (implicit: `false`) | `true` |

```yaml
action: vehicule.actualizeaza_rca
data:
  nr_inmatriculare: "B123ABC"
  numar_polita: "RCA-2026-123456"
  companie: "Euroins"
  data_emitere: "2026-04-01"
  data_expirare: "2027-04-01"
  cost: 1500
  arhivare: true
```

### vehicule.actualizeaza_casco

Actualizează datele asigurării CASCO pentru un vehicul.

| Parametru | Tip | Obligatoriu | Descriere | Exemplu |
|-----------|-----|-------------|-----------|---------|
| `nr_inmatriculare` | string | Da | Placa vehiculului | `B123ABC` |
| `numar_polita` | string | Nu | Numărul poliței | `CASCO-2026-789012` |
| `companie` | string | Nu | Compania de asigurare | `Allianz-Țiriac` |
| `data_emitere` | string | Nu | Data emiterii | `2026-04-01` |
| `data_expirare` | string | Nu | Data expirării | `2027-04-01` |
| `cost` | float | Nu | Cost în RON (0–99.999) | `3500` |
| `arhivare` | bool | Nu | Arhivează datele vechi (implicit: `false`) | `true` |

```yaml
action: vehicule.actualizeaza_casco
data:
  nr_inmatriculare: "B123ABC"
  numar_polita: "CASCO-2026-789012"
  companie: "Allianz-Țiriac"
  data_emitere: "2026-04-01"
  data_expirare: "2027-04-01"
  cost: 3500
  arhivare: true
```

> **Notă**: Serviciile de actualizare documente fac **merge** — actualizează doar câmpurile transmise, fără a șterge datele existente. Toate câmpurile în afară de `nr_inmatriculare` sunt opționale.

---

## Exemple de automatizări

### Actualizare km din senzor OBD/GPS

```yaml
automation:
  - alias: "Actualizare km din OBD/GPS"
    triggers:
      - trigger: time_pattern
        hours: "/1"
    actions:
      - action: vehicule.actualizeaza_date
        data:
          nr_inmatriculare: "B123ABC"
          km_curent: "{{ states('sensor.obd_odometer') | int(0) }}"
```

### Notificare documente care expiră

```yaml
automation:
  - alias: "Vehicul B123ABC — Notificări zilnice"
    triggers:
      - trigger: time
        at: "11:00:00"
    actions:
      - repeat:
          for_each:
            - entity: sensor.vehicule_b123abc_rca
              name: "RCA"
              prag: 30
              unitate: "zile"
            - entity: sensor.vehicule_b123abc_itp
              name: "ITP"
              prag: 30
              unitate: "zile"
            - entity: sensor.vehicule_b123abc_revizie_ulei
              name: "Revizie ulei"
              prag: 1000
              unitate: "km"
            - entity: sensor.vehicule_b123abc_placute_frana
              name: "Plăcuțe frână"
              prag: 3000
              unitate: "km"
          sequence:
            - variables:
                val: "{{ states(repeat.item.entity) }}"
            - if:
                - condition: template
                  value_template: >
                    {{ val not in ['unknown', 'unavailable'] and val | int(999) < repeat.item.prag }}
              then:
                - action: notify.mobile_app
                  data:
                    title: "⚠️ {{ repeat.item.name }} — B123ABC"
                    message: "Mai ai {{ val }} {{ repeat.item.unitate }} rămase."
```

> **Notă**: Înlocuiți `notify.mobile_app` cu serviciul vostru de notificare. Lista de senzori și pragurile se pot ajusta.

### Sincronizare rovinieta din eRovinieta (CNAIR)

Dacă folosiți integrarea [eRovinieta](https://github.com/cnecrea/erovinieta), puteți sincroniza automat datele rovinietei:

```yaml
automation:
  - alias: "Sincronizare rovinieta eRovinieta → Vehicule"
    triggers:
      - trigger: state
        entity_id: sensor.cnair_erovinieta_rovinieta_activa_b123abc
    conditions:
      - condition: template
        value_template: >
          {{ state_attr('sensor.cnair_erovinieta_rovinieta_activa_b123abc',
             'Data început vignietă') is not none }}
    actions:
      - action: vehicule.actualizeaza_rovinieta
        data:
          nr_inmatriculare: "B123ABC"
          data_inceput: >
            {{ state_attr('sensor.cnair_erovinieta_rovinieta_activa_b123abc',
               'Data început vignietă') }}
          data_sfarsit: >
            {{ state_attr('sensor.cnair_erovinieta_rovinieta_activa_b123abc',
               'Data sfârșit vignietă') }}
          categorie: >
            {{ state_attr('sensor.cnair_erovinieta_rovinieta_activa_b123abc',
               'Categorie vignietă') }}
          arhivare: true
```

> Formatul `2026-03-12 09:52:47` primit de la eRovinieta este acceptat automat — serviciul extrage doar data.

---

## Carduri Lovelace

### Card cu entități

```yaml
type: entities
title: Vehicul B123ABC
entities:
  - sensor.vehicule_b123abc_informatii
  - sensor.vehicule_b123abc_kilometraj
  - sensor.vehicule_b123abc_rca
  - sensor.vehicule_b123abc_itp
  - sensor.vehicule_b123abc_cost_total
```

### Card cu auto-entities (toate entitățile)

```yaml
type: custom:auto-entities
filter:
  include:
    - entity_id: "sensor.vehicule_b123abc*"
title: Vehicul B123ABC — Toate
```

---

## Diagnostics

1. **Setări** → **Dispozitive și servicii** → click pe vehicul
2. Click pe cele 3 puncte (⋮) → **Download diagnostics**

Datele sunt structurate pe categorii (identificare, kilometraj, rca, casco, itp, rovinieta, administrativ, revizie_ulei, distributie, anvelope, baterie, frane, echipament_obligatoriu), cu secțiune separată pentru istoric și lista senzorilor activi.

Informațiile sensibile (VIN, serie CIV, nr. înmatriculare, nr. poliță, proprietar) sunt mascate automat.

---

## Verificare după instalare

1. **Setări** → **Dispozitive și servicii** → **Dispozitive** — căutați dispozitivul cu placa vehiculului
2. **Setări** → **Dispozitive și servicii** → **Entități** — filtrați după `sensor.vehicule_` și verificați senzorii creați
3. **Setări** → **Sistem** → **Jurnale** — filtrați după `vehicule` și verificați că nu sunt erori
4. Testați serviciile din **Instrumente pentru dezvoltatori** → **Servicii** (ex: `vehicule.actualizeaza_date`, `vehicule.actualizeaza_rovinieta`, `vehicule.actualizeaza_itp`, `vehicule.actualizeaza_rca`, `vehicule.actualizeaza_casco`)

---

## Dezinstalare

### Prin HACS

1. **HACS** → localizați **„Vehicule"** → **Dezinstalare**
2. Reporniți Home Assistant

### Manual

1. Ștergeți folderul `vehicule` din `config/custom_components/`
2. Reporniți Home Assistant
3. Ștergeți integrarea din **Setări** → **Dispozitive și servicii** dacă apare

---

## Suport

Pentru probleme sau sugestii: https://github.com/cnecrea/vehicule/issues

---

**Versiune:** 1.3.0
**Compatibilitate:** Home Assistant 2025.11.0+
