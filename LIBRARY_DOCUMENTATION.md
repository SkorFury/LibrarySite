# Bibliotēkas Pārvaldības Sistēma

Šī ir visaptveroša bibliotēkas pārvaldības sistēma, kas izstrādāta ar Flask un SQLAlchemy, nodrošinot visas nepieciešamās funkcijas grāmatu kolekcijas un lietotāju aizņēmumu pārvaldībai.

## Funkcionalitātes

### 1. Grāmatu pārvaldība
- **Pievienot grāmatas**: Administratori var pievienot jaunas grāmatas ar šādām detaļām:
   - Nosaukums
   - Autors
   - ISBN
   - Izdevējs
   - Gads
   - Kategorija
   - Kopiju skaits
   - Apraksts

- **Meklēt grāmatas**: Meklēšana pēc nosaukuma, autora vai ISBN
- **Filtrēt pēc kategorijas**: Pārlūkot grāmatas pēc kategorijas
- **Rediģēt/dzēst grāmatas**: Administratori var atjaunināt vai dzēst grāmatas

### 2. Lietotāju pārvaldība
- Lietotāju reģistrācija un pieteikšanās sistēma
- Lietotāju profili ar pielāgojamiem iestatījumiem
- Divas lietotāju lomas:
   - Parastie lietotāji (var aizņemties un rezervēt grāmatas)
   - Administratori (var pārvaldīt grāmatas, lietotājus, aizņēmumus un rezervācijas)

### 3. Aizņēmumu sistēma
- **Aizņemties grāmatas**: Lietotāji var aizņemties pieejamās grāmatas
- **Aizņēmuma periods**: 14 dienas
- **Atgriezt grāmatas**: Atzīmēt grāmatas kā atgrieztas
- **Statusa izsekošana**: Aktīvie, atgrieztie un kavētie aizņēmumi
- **Mani aizņēmumi**: Lietotāji var skatīt savus pašreizējos un iepriekšējos aizņēmumus
- **Administratora aizņēmumu pārvaldība**: Administratori var skatīt un pārvaldīt visus aizņēmumus

### 4. Rezervāciju sistēma
- **Rezervēt grāmatas**: Lietotāji var rezervēt grāmatas, ja visas kopijas ir izsniegtas
- **Rezervācijas termiņš**: Rezervācijas beidzas pēc 7 dienām
- **Automātiska izpilde**: Rezervācijas tiek automātiski atzīmētas kā izpildītas, kad lietotājs aizņemas grāmatu
- **Manas rezervācijas**: Lietotāji var skatīt un atcelt savas rezervācijas
- **Administratora rezervāciju pārvaldība**: Administratori var skatīt visas neizpildītās rezervācijas

## Datu struktūra un modeļi

### Datu bāzes shēma

#### Grāmatas modelis
```python
- id (Primārā atslēga)
- title (Virkne, obligāts)
- author (Virkne, obligāts)
- isbn (Virkne, unikāls, obligāts)
- publisher (Virkne, nav obligāts)
- year (Vesels skaitlis, nav obligāts)
- copies_total (Vesels skaitlis, noklusējums: 1)
- copies_available (Vesels skaitlis, noklusējums: 1)
- category (Virkne, nav obligāts)
- description (Teksts, nav obligāts)
- date_added (Datums/laiks, noklusējums: tagad)
```


#### Lietotāja modelis
```python
- id (Primārā atslēga)
- username (Virkne, unikāls, obligāts)
- password_hash (Virkne, obligāts)
- email (Virkne, nav obligāts)
- role (Virkne, noklusējums: 'user')
- profile_pic (Virkne, nav obligāts)
```

#### Aizņēmuma modelis
```python
- id (Primārā atslēga)
- book_id (Ārējā atslēga -> Grāmata)
- user_id (Ārējā atslēga -> Lietotājs)
- loan_date (Datums/laiks, noklusējums: tagad)
- due_date (Datums/laiks, obligāts)
- return_date (Datums/laiks, var būt tukšs)
- status (Virkne: 'active', 'returned', 'overdue')
```

#### Rezervācijas modelis
```python
- id (Primārā atslēga)
- book_id (Ārējā atslēga -> Grāmata)
- user_id (Ārējā atslēga -> Lietotājs)
- reservation_date (Datums/laiks, noklusējums: tagad)
- expiry_date (Datums/laiks, var būt tukšs)
- status (Virkne: 'pending', 'fulfilled', 'cancelled')
```

### Attiecības
- Grāmata ↔ Aizņēmums (viens pret daudziem)
- Lietotājs ↔ Aizņēmums (viens pret daudziem)
- Grāmata ↔ Rezervācija (viens pret daudziem)
- Lietotājs ↔ Rezervācija (viens pret daudziem)

## Datu glabāšanas sistēma

### Tehnoloģiju izvēle: SQL datubāze (SQLite)

**Izvēlētā sistēma**: SQLite datubāze ar SQLAlchemy ORM

**Kāpēc izvēlēties SQL, nevis alternatīvas**:

1. **Datu konsekvence**:
   - ACID īpašības nodrošina datu integritāti
   - Ārējo atslēgu ierobežojumi uztur saistību integritāti
   - Transakcijas novērš datu bojājumus

2. **Attiecību pārvaldība**:
   - Dabisks atbalsts sarežģītām attiecībām (lietotāji, grāmatas, aizņēmumi, rezervācijas)
   - Efektīvas JOIN operācijas saistīto datu vaicāšanai
   - Viegli uzturēt datu konsekvenci starp tabulām

3. **Mērogojamība**:
   - Viegli migrēt uz lielākām SQL datubāzēm (PostgreSQL, MySQL), ja bibliotēka aug
   - Indeksēti vaicājumi nodrošina ātru meklēšanu
   - Atbalsts vairākiem vienlaicīgiem lietotājiem

4. **Vaicājumu elastība**:
   - Sarežģīti vaicājumi ar filtrēšanu, kārtošanu un apkopošanu
   - Pilnteksta meklēšanas iespējas
   - Viegli ģenerēt atskaites un statistiku

## Datu struktūru realizācija

### Programmēšanas valoda: Python

**Izmantotās galvenās datu struktūras**:

1. **Klases (OOP)**:
   - Grāmata, Lietotājs, Aizņēmums, Rezervācija (SQLAlchemy ORM)
   - Datu un uzvedības kapsulēšana
   - Mantots no `db.Model` bāzes klases

2. **Vārdnīca/Hash tabula**:
   - Sesiju pārvaldība izmanto vārdnīcas
   - Ātra O(1) piekļuve lietotāju datiem
   - Formu datu apstrāde ar request.form vārdnīcu

3. **Saraksti/Masīvi**:
   - Vaicājumu rezultāti tiek atgriezti kā saraksti
   - Efektīva iterācija kolekciju attēlošanai
   - Atbalsts filtrēšanai un kārtošanai

### Galvenās funkcijas

**Grāmatu pārvaldība**:
```python
def add_book()        # Pievieno jaunu grāmatu bibliotēkai
def edit_book(id)     # Atjaunina grāmatas informāciju
def delete_book(id)   # Dzēš grāmatu no kataloga
def view_book(id)     # Parāda grāmatas detaļas
def library()         # Meklē un pārlūko grāmatas
```

**Aizņēmumu pārvaldība**:
```python
def borrow_book(id)   # Izveido jaunu aizņēmumu
def return_book(id)   # Atzīmē grāmatu kā atgrieztu
def my_loans()        # Skatīt lietotāja aizņēmumus
def admin_loans()     # Administratora skats visiem aizņēmumiem
```

**Rezervāciju pārvaldība**:
```python
def reserve_book(id)         # Izveido rezervāciju
def cancel_reservation(id)   # Atceļ rezervāciju
def my_reservations()        # Skatīt lietotāja rezervācijas
def admin_reservations()     # Administratora skats visām rezervācijām
```

## Meklēšana un veiktspēja

### Meklēšanas realizācija
- **Teksta meklēšana**: Izmanto SQL LIKE operatoru elastīgai atbilstībai
- **Filtrēšana pēc kategorijas**: Precīza atbilstība kategorijas laukam
- **Kombinētā meklēšana**: Meklēšana vairākos laukos (nosaukums, autors, ISBN)
- **Veiktspēja**: Indeksēti lauki ātrai meklēšanai

### Datu piekļuves modeļi
- **O(1)** - Lietotāja sesijas meklēšana (vārdnīca)
- **O(log n)** - Grāmatas meklēšana pēc ISBN (indeksēts)
- **O(n)** - Filtrēšana pēc kategorijas (tabulas skenēšana)
- **O(n log n)** - Kārtotu grāmatu sarakstu iegūšana

## Instalācija un uzstādīšana

1. **Instalēt atkarības**:
```bash
pip install -r requirements.txt
```

2. **Palaist lietotni**:
```bash
python app.py
```

3. **Piekļūt vietnei**:
   - Atveriet pārlūkā `http://127.0.0.1:5000`
   - Noklusējuma ports: 5000

4. **Izveidot administratora lietotāju**:
   - Pirmais lietotājs jāizveido ar administratora lomu
   - Izmantojiet administratora paneli, lai izveidotu papildu lietotājus

## Lietošana

### Lietotājiem:
1. Reģistrējieties/piesakieties savā kontā
2. Pārlūkojiet bibliotēkas katalogu
3. Aizņemieties pieejamās grāmatas (14 dienas)
4. Rezervējiet grāmatas, ja tās nav pieejamas
5. Skatiet savus aktīvos aizņēmumus un rezervācijas
6. Atgrieziet grāmatas pēc izlasīšanas

### Administratoriem:
1. Pievienojiet jaunas grāmatas bibliotēkai
2. Rediģējiet grāmatu informāciju
3. Pārvaldiet lietotāju kontus
4. Uzraugiet visus aizņēmumus un kavētos priekšmetus
5. Skatiet visas rezervācijas
6. Dzēsiet grāmatas (tikai, ja nav aktīvu aizņēmumu)

## Tehniskā informācija

### Sesiju pārvaldība
- Flask sesijas glabā lietotāja autentifikācijas stāvokli
- Droša paroļu hashēšana ar Werkzeug
- Lomu balstīta piekļuves kontrole

### Datu bāzes noturība
- SQLite datubāzes fails: `instance/users.db`
- Dati saglabājas starp sesijām
- Automātiska tabulu izveide pirmajā palaišanas reizē
- Atbalsts shēmas migrācijām

### Kļūdu apstrāde
- Ievades validācija visās formās
- Dublikātu ISBN novēršana
- Aktīvu aizņēmumu pārbaude pirms dzēšanas
- Kavēto aizņēmumu noteikšana un atzīmēšana

## Nākotnes uzlabojumi

Iespējamie uzlabojumi:
- E-pasta paziņojumi par termiņiem
- Svītrkodu skenēšana ISBN ievadei
- Grāmatu vāku attēli
- Lasīšanas ieteikumi
- Statistikas panelis
- Eksporta funkcionalitāte
- Mobilās lietotnes integrācija

## Autors
Izstrādāts kā bibliotēkas pārvaldības sistēmas projekts, demonstrējot datu struktūras, datubāzu pārvaldību un tīmekļa lietotņu izstrādi.
