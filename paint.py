import cv2
import numpy as np
import tkinter as tk
from tkinter import colorchooser, filedialog, Menu
from PIL import Image, ImageTk

# Konfiguracja wymiarów
szerokosc_plotna = 800
wysokosc_plotna = 600
szerokosc_panelu = 200
szerokosc_okna = szerokosc_plotna + szerokosc_panelu
wysokosc_okna = wysokosc_plotna

# Inicjalizacja płótna
plotno = np.ones((wysokosc_plotna, szerokosc_plotna, 3), dtype=np.uint8) * 255

# Zmienne globalne
aktualne_narzedzie = 'pędzel'
narzedzie_rysowania = None
aktualny_kolor = (0, 0, 0)
rozmiar_pedzla = 5
rysowanie = False
ostatni_punkt = None
punkt_startowy = None

# Kolory w palecie (BGR)
kolory = [
    (0, 0, 0), (0, 0, 255), (0, 255, 0), (255, 0, 0),
    (255, 255, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)
]

# Lista narzędzi i operacji
narzedzia = ['pędzel', 'gumka', 'prostokąt', 'koło', 'trójkąt prostokątny', 'trójkąt równoramienny', 'wybierz kolor',
             'wypełnianie']
operacje = ['Zmień tło', 'Zapisz', 'Otwórz obraz']


def aktualizuj_plotno():
    obraz = cv2.cvtColor(plotno, cv2.COLOR_BGR2RGB)
    obraz = Image.fromarray(obraz)
    obraz = ImageTk.PhotoImage(image=obraz)
    etykieta_plotna.config(image=obraz)
    etykieta_plotna.image = obraz


def rysuj_panel():
    for widget in ramka_panelu.winfo_children():
        widget.destroy()

    # Przyciski narzędzi
    for narzedzie in narzedzia:
        przycisk = tk.Button(ramka_panelu, text=narzedzie, command=lambda n=narzedzie: ustaw_narzedzie(n))
        przycisk.pack(fill=tk.X, pady=2)

    # Paleta kolorów
    ramka_kolorow = tk.Frame(ramka_panelu)
    ramka_kolorow.pack(fill=tk.X, pady=10)
    for i, kolor in enumerate(kolory):
        przycisk = tk.Button(ramka_kolorow, bg=f'#{kolor[2]:02x}{kolor[1]:02x}{kolor[0]:02x}',
                             width=3, command=lambda c=kolor: ustaw_kolor(c))
        przycisk.grid(row=i // 2, column=i % 2, padx=2, pady=2)

    # Suwak do zmiany rozmiaru pędzla
    ramka_rozmiaru = tk.Frame(ramka_panelu)
    ramka_rozmiaru.pack(fill=tk.X, pady=10)
    tk.Label(ramka_rozmiaru, text="Rozmiar pędzla:").pack()
    suwak = tk.Scale(ramka_rozmiaru, from_=1, to=50, orient=tk.HORIZONTAL,
                     command=lambda v: ustaw_rozmiar_pedzla(int(v)))
    suwak.set(rozmiar_pedzla)
    suwak.pack(fill=tk.X)

    # Przyciski operacji
    for op in operacje:
        przycisk = tk.Button(ramka_panelu, text=op, command=lambda o=op: wykonaj_operacje(o))
        przycisk.pack(fill=tk.X, pady=2)


def ustaw_narzedzie(narzedzie):
    global aktualne_narzedzie, punkt_startowy
    aktualne_narzedzie = narzedzie
    punkt_startowy = None
    aktualizuj_plotno()


def ustaw_kolor(kolor):
    global aktualny_kolor
    aktualny_kolor = kolor


def ustaw_rozmiar_pedzla(rozmiar):
    global rozmiar_pedzla
    rozmiar_pedzla = rozmiar


def wykonaj_operacje(operacja):
    global plotno
    if operacja == 'Zmień tło':
        plotno[:, :] = aktualny_kolor
        aktualizuj_plotno()
    elif operacja == 'Zapisz':
        sciezka = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("Wszystkie pliki", "*.*")]
        )
        if sciezka:
            cv2.imwrite(sciezka, plotno)
    elif operacja == 'Otwórz obraz':
        sciezka = filedialog.askopenfilename(
            filetypes=[("Obrazy", "*.png;*.jpg;*.jpeg;*.bmp"), ("Wszystkie pliki", "*.*")]
        )
        if sciezka:
            try:
                nowy_obraz = cv2.imread(sciezka)
                if nowy_obraz is not None:
                    h, w = nowy_obraz.shape[:2]
                    skala = min(szerokosc_plotna / w, wysokosc_plotna / h)
                    nowy_rozmiar = (int(w * skala), int(h * skala))
                    przeskalowany = cv2.resize(nowy_obraz, nowy_rozmiar, interpolation=cv2.INTER_AREA)

                    # Wyśrodkuj obraz na płótnie
                    y = (wysokosc_plotna - przeskalowany.shape[0]) // 2
                    x = (szerokosc_plotna - przeskalowany.shape[1]) // 2

                    plotno[y:y + przeskalowany.shape[0], x:x + przeskalowany.shape[1]] = przeskalowany
                    aktualizuj_plotno()
            except Exception as e:
                print(f"Błąd wczytywania obrazu: {str(e)}")


def wypelnij_obszar(x, y):
    h, w = plotno.shape[:2]
    maska = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(plotno, maska, (x, y), aktualny_kolor, loDiff=(10, 10, 10), upDiff=(10, 10, 10))
    aktualizuj_plotno()


def obsluga_myszy(event):
    global plotno, aktualny_kolor, rozmiar_pedzla, rysowanie, ostatni_punkt, punkt_startowy, narzedzie_rysowania

    x, y = event.x, event.y

    try:
        if 0 <= x < szerokosc_plotna and 0 <= y < wysokosc_plotna:
            if event.num == 1:
                if aktualne_narzedzie in ['pędzel', 'gumka']:
                    rysowanie = True
                    ostatni_punkt = (x, y)
                elif aktualne_narzedzie in ['prostokąt', 'koło', 'trójkąt prostokątny', 'trójkąt równoramienny']:
                    punkt_startowy = (x, y)
                    narzedzie_rysowania = aktualne_narzedzie
                elif aktualne_narzedzie == 'wybierz kolor':
                    aktualny_kolor = tuple(map(int, plotno[y, x]))
                    ustaw_narzedzie('pędzel')
                elif aktualne_narzedzie == 'wypełnianie':
                    wypelnij_obszar(x, y)

            elif event.type == tk.EventType.Motion:
                if rysowanie and aktualne_narzedzie in ['pędzel', 'gumka'] and ostatni_punkt:
                    kolor = aktualny_kolor if aktualne_narzedzie == 'pędzel' else (255, 255, 255)
                    cv2.line(plotno, ostatni_punkt, (x, y), kolor, rozmiar_pedzla)
                    ostatni_punkt = (x, y)
                    aktualizuj_plotno()
                elif punkt_startowy and narzedzie_rysowania in ['prostokąt', 'koło', 'trójkąt prostokątny',
                                                                'trójkąt równoramienny']:
                    tymczasowy_obraz = plotno.copy()
                    grubosc = -1 if rozmiar_pedzla == 0 else rozmiar_pedzla

                    if narzedzie_rysowania == 'prostokąt':
                        cv2.rectangle(tymczasowy_obraz, punkt_startowy, (x, y), aktualny_kolor, grubosc)
                    elif narzedzie_rysowania == 'koło':
                        promien = int(np.hypot(x - punkt_startowy[0], y - punkt_startowy[1]))
                        cv2.circle(tymczasowy_obraz, punkt_startowy, promien, aktualny_kolor, grubosc)
                    elif narzedzie_rysowania == 'trójkąt prostokątny':
                        punkty = np.array([punkt_startowy, (punkt_startowy[0], y), (x, y)], np.int32)
                        cv2.polylines(tymczasowy_obraz, [punkty], True, aktualny_kolor, grubosc)
                    elif narzedzie_rysowania == 'trójkąt równoramienny':
                        srodek_x = (punkt_startowy[0] + x) // 2
                        punkty = np.array(
                            [punkt_startowy, (srodek_x, punkt_startowy[1] - (x - punkt_startowy[0])), (x, y)], np.int32)
                        cv2.polylines(tymczasowy_obraz, [punkty], True, aktualny_kolor, grubosc)

                    obraz = cv2.cvtColor(tymczasowy_obraz, cv2.COLOR_BGR2RGB)
                    obraz = Image.fromarray(obraz)
                    obraz = ImageTk.PhotoImage(image=obraz)
                    etykieta_plotna.config(image=obraz)
                    etykieta_plotna.image = obraz

            elif event.type == tk.EventType.ButtonRelease and event.num == 1:
                rysowanie = False
                if punkt_startowy and narzedzie_rysowania in ['prostokąt', 'koło', 'trójkąt prostokątny',
                                                              'trójkąt równoramienny']:
                    grubosc = -1 if rozmiar_pedzla == 0 else rozmiar_pedzla

                    if narzedzie_rysowania == 'prostokąt':
                        cv2.rectangle(plotno, punkt_startowy, (x, y), aktualny_kolor, grubosc)
                    elif narzedzie_rysowania == 'koło':
                        promien = int(np.hypot(x - punkt_startowy[0], y - punkt_startowy[1]))
                        cv2.circle(plotno, punkt_startowy, promien, aktualny_kolor, grubosc)
                    elif narzedzie_rysowania == 'trójkąt prostokątny':
                        punkty = np.array([punkt_startowy, (punkt_startowy[0], y), (x, y)], np.int32)
                        cv2.fillPoly(plotno, [punkty], aktualny_kolor)
                    elif narzedzie_rysowania == 'trójkąt równoramienny':
                        srodek_x = (punkt_startowy[0] + x) // 2
                        punkty = np.array(
                            [punkt_startowy, (srodek_x, punkt_startowy[1] - (x - punkt_startowy[0])), (x, y)], np.int32)
                        cv2.fillPoly(plotno, [punkty], aktualny_kolor)

                    aktualizuj_plotno()
                punkt_startowy = None
                narzedzie_rysowania = None

    except Exception as e:
        print(f"Błąd obsługi myszy: {str(e)}")


# Inicjalizacja interfejsu
root = tk.Tk()
root.title("Program do rysowania")
root.geometry(f"{szerokosc_okna}x{wysokosc_okna}")

# Menu
pasek_menu = Menu(root)
menu_plik = Menu(pasek_menu, tearoff=0)
menu_plik.add_command(label="Zapisz", command=lambda: wykonaj_operacje('Zapisz'))
menu_plik.add_command(label="Otwórz obraz", command=lambda: wykonaj_operacje('Otwórz obraz'))
menu_plik.add_separator()
menu_plik.add_command(label="Wyjdź", command=root.quit)
pasek_menu.add_cascade(label="Plik", menu=menu_plik)
root.config(menu=pasek_menu)

# Interfejs główny
ramka_plotna = tk.Frame(root, width=szerokosc_plotna, height=wysokosc_plotna)
ramka_plotna.pack(side=tk.LEFT)
ramka_panelu = tk.Frame(root, width=szerokosc_panelu, height=wysokosc_plotna)
ramka_panelu.pack(side=tk.RIGHT, fill=tk.Y)

# Inicjalizacja wyświetlacza
obraz = cv2.cvtColor(plotno, cv2.COLOR_BGR2RGB)
obraz = Image.fromarray(obraz)
obraz = ImageTk.PhotoImage(image=obraz)
etykieta_plotna = tk.Label(ramka_plotna, image=obraz)
etykieta_plotna.pack()

# Podpięcie zdarzeń
etykieta_plotna.bind("<Button-1>", obsluga_myszy)
etykieta_plotna.bind("<B1-Motion>", obsluga_myszy)
etykieta_plotna.bind("<ButtonRelease-1>", obsluga_myszy)

rysuj_panel()
root.mainloop()