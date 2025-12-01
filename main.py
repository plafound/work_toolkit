#!/usr/bin/env python3
import os
from modules import watermark, merge, split, compress, rotate, convert

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    input("\nTekan ENTER untuk kembali...")
    clear_screen()

def main_menu():
    MENU = {
        "1": ("Watermark PDF", watermark.run_watermark),
        "2": ("Merge PDF", merge.run_merge),
        "3": ("Split PDF", split.run_split),
        "4": ("Compress PDF/IMAGE", compress.run_compress),
        "5": ("Rotate PDF", rotate.run_rotate),
        "6": ("Convert PDF / Image / Word / Excel", convert.run_convert),
        "0": ("Keluar", None)
    }

    while True:
        clear_screen()
        print("=== PDF TOOLKIT ===\n")
        for k, (desc, _) in MENU.items():
            print(f"{k}. {desc}")
        choice = input("\nPilih menu: ").strip()

        if choice == "0":
            break
        elif choice in MENU:
            clear_screen()
            try:
                MENU[choice][1]()
            except Exception as e:
                print(f"\n❌ Terjadi kesalahan: {e}")
            pause()
        else:
            print("Pilihan tidak valid.")
            pause()

if __name__ == "__main__":
    main_menu()