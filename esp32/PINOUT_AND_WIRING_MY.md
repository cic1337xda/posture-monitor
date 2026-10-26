# 🔌 Spesifikasi Sambungan Litar & Pinout Hardware (`PINOUT_AND_WIRING_MY.md`)

Dokumen ini menyediakan pelan sambungan litar terperinci, spesifikasi komponen, dan pemetaan pin bagi **Peranti Haptik Boleh Pakai Posture AI** berasaskan mikropengawal **ESP32-C3**.

---

## 📌 Jadual Penetapan Pin Hardware

| Pin Mikropengawal | Sambungan Komponen | Penerangan Isyarat | Ciri-ciri Elektrik |
| :--- | :--- | :--- | :--- |
| **`GPIO 8`** | Tapak Transistor ($R_1$) | Picu Haptik PWM / LED Terbina Dalam | Logik 3.3V HIGH aktif, serentak dengan LED biru atas papan |
| **`3.3V` / `5V`** | Motor (+) & Katod Diod | Rel Kuasa Positif | Membekalkan arus operasi motor (~70mA arus puncak) |
| **`GND`** | Pengeluar Transistor (E)| Rujukan Bumi Sepunya | Rel ground sistem |
| **Motor (-)** | Pemungut Transistor (C)| Suis Arus Bumi | Ditarik ke paras LOW apabila `GPIO 8` bernilai HIGH |

---

## 📐 Gambar Rajah Litar Skematik

Peranti wearable menggunakan suis transistor **NPN low-side** yang dilengkapi diod perlindungan flyback:

<p align="center">
  <img src="Schematic_posturemonitor_2026-10-26.png" width="820" alt="Litar Skematik Wearable ESP32-C3 Posture AI" />
</p>

* 📄 **Muat Turun Skematik PDF Boleh Cetak:** [`Schematic_posturemonitor_2026-10-26.pdf`](Schematic_posturemonitor_2026-10-26.pdf)

---

## 🧩 Senarai Bahan & Komponen (BOM)

| Bil | Penerangan Komponen | Model Disyorkan | Fungsi |
| :---: | :--- | :--- | :--- |
| **1** | Mikropengawal ESP32-C3 RISC-V | ESP32-C3 SuperMini / Xiao ESP32C3 | Unit pemprosesan utama, klien WiFi, dan pelanggan MQTT |
| **2** | Motor Getar Duit Syiling (*Coin Disc*) | 1027 / 1030 3V DC Motor | Menjana maklum balas getaran fizikal pada pergelangan tangan |
| **3** | Transistor Suis NPN | 2N2222 / 2N3904 / S8050 | Menguatkan arus GPIO rendah untuk memacu motor (~70mA) |
| **4** | Perintang Had Arus Tapak (*Base*) | $1\,\text{k}\Omega$ ($0.25\text{W}$) | Mengehadkan arus tapak kepada $\approx 2.6\text{mA}$ untuk lindungi GPIO |
| **5** | Diod Perlindungan Flyback | 1N4001 / 1N4148 | Menyerap lonjakan voltan induktif (*back-EMF*) semasa motor berhenti |
| **6** | Sumber Kuasa | Bateri LiPo 3.7V atau USB-C 5V | Bekalan kuasa mudah alih atau kabel sambungan terus |

---

## ⚠️ Prinsip Perlindungan Hardware

1. **Larangan Sambungan Terus ke Pin GPIO:**
   Pin GPIO ESP32-C3 hanya mampu membekalkan arus maksimum **$20\text{mA}$**. Motor getar memerlukan arus antara **$60\text{mA}$ hingga $90\text{mA}$**. Menyambungkan motor secara terus ke pin GPIO akan merosakkan cip mikropengawal secara kekal.
2. **Perlindungan Lonjakan Arus Diod Flyback:**
   Beban induktif seperti motor menghasilkan lonjakan voltan songsang ($V = -L \frac{di}{dt}$) melepasi 30V apabila dimatikan secara mendadak. **Diod 1N4001** yang dipasang secara selari merentasi terminal motor akan menyerap dan mengepit lonjakan arus ini dengan selamat.
3. **Penstabilan Kuasa & RF dalam Firmware:**
   - Arahan `btStop()` dipanggil serta-merta dalam fungsi `setup()` untuk mematikan modul Bluetooth, sekali gus menjimatkan arus puncak.
   - Kuasa pemancar WiFi dihadkan kepada $8.5\,\text{dBm}$ menggunakan `WiFi.setTxPower(WIFI_POWER_8_5dBm)` bagi mengelakkan masalah *brownout reset* pada pengawal selia voltan kecil.
