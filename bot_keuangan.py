from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

TOKEN = "8870452198:AAGkmJlaasZlE2UWxb7-TD8QnXOPLTjvBxU"

# ==========================
# GOOGLE SHEETS
# ==========================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "bot-keuangan-498215-3a10fa44ff29.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)

sheet = client.open("Catatan Keuangan").sheet1

# ==========================
# KATEGORI OTOMATIS
# ==========================

KATEGORI = {
    "kopi": "Minuman",
    "teh": "Minuman",
    "minum": "Minuman",

    "makan": "Makanan",
    "nasi": "Makanan",
    "gorengan": "Makanan",

    "bensin": "Transportasi",
    "parkir": "Transportasi",
    "oli": "Transportasi",
    "service": "Transportasi",

    "rokok": "Rokok",
    "catridge": "Rokok",

    "gaji": "Pendapatan",
    "profit": "Pendapatan",
    "airdrop": "Pendapatan",
}

def cari_kategori(deskripsi):

    teks = deskripsi.lower()

    for kata, kategori in KATEGORI.items():

        if kata in teks:
            return kategori

    return "Lainnya"

# ==========================
# INPUT TRANSAKSI
# ==========================

async def simpan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    pesan = update.message.text.strip().lower()

    data = pesan.split()

    if len(data) < 3:
        return

    if data[0] not in ["masuk", "keluar"]:
        return

    try:
        nominal = int(data[1])
    except:
        await update.message.reply_text(
            "Contoh:\n\nkeluar 5000 kopi\nmasuk 500000 gaji"
        )
        return

    jenis = data[0].capitalize()
    deskripsi = " ".join(data[2:])
    kategori = cari_kategori(deskripsi)

    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        jenis,
        nominal,
        deskripsi,
        kategori
    ])

    await update.message.reply_text(
        f"✅ Tercatat\n\n"
        f"Jenis : {jenis}\n"
        f"Nominal : Rp{nominal:,}\n"
        f"Kategori : {kategori}"
    )

# ==========================
# SALDO
# ==========================

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = sheet.get_all_values()

    masuk = 0
    keluar = 0

    for row in data[1:]:

        try:

            if row[1] == "Masuk":
                masuk += int(row[2])

            elif row[1] == "Keluar":
                keluar += int(row[2])

        except:
            pass

    total = masuk - keluar

    await update.message.reply_text(
        f"💰 Saldo Saat Ini\n\nRp{total:,}"
    )

# ==========================
# LAPORAN SEMUA DATA
# ==========================

async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = sheet.get_all_values()

    masuk = 0
    keluar = 0

    kategori_total = {}

    for row in data[1:]:

        try:

            jenis = row[1]
            nominal = int(row[2])
            kategori = row[4]

            if jenis == "Masuk":
                masuk += nominal

            elif jenis == "Keluar":

                keluar += nominal

                kategori_total[kategori] = (
                    kategori_total.get(kategori, 0)
                    + nominal
                )

        except:
            pass

    saldo_akhir = masuk - keluar

    rasio = 1

    if masuk > 0:
        rasio = keluar / masuk

    if rasio > 0.8:
        status = "🔴 BOROS"
    elif rasio > 0.5:
        status = "🟡 NORMAL"
    else:
        status = "🟢 HEMAT"

    terbesar = "-"

    if kategori_total:
        terbesar = max(
            kategori_total,
            key=kategori_total.get
        )

    await update.message.reply_text(
        f"📊 LAPORAN\n\n"
        f"💰 Pemasukan : Rp{masuk:,}\n"
        f"💸 Pengeluaran : Rp{keluar:,}\n"
        f"💵 Saldo : Rp{saldo_akhir:,}\n\n"
        f"🏆 Kategori Terbesar : {terbesar}\n"
        f"📈 Status : {status}"
    )

# ==========================
# LAPORAN BULAN INI
# ==========================

async def bulan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = sheet.get_all_values()

    bulan_ini = datetime.now().month
    tahun_ini = datetime.now().year

    total_masuk = 0
    total_keluar = 0

    for row in data[1:]:

        try:

            tanggal = datetime.strptime(
                row[0],
                "%Y-%m-%d %H:%M:%S"
            )

            if (
                tanggal.month == bulan_ini
                and tanggal.year == tahun_ini
            ):

                nominal = int(row[2])

                if row[1] == "Masuk":
                    total_masuk += nominal

                elif row[1] == "Keluar":
                    total_keluar += nominal

        except:
            pass

    saldo_bulan = total_masuk - total_keluar

    await update.message.reply_text(
        f"📅 BULAN INI\n\n"
        f"💰 Masuk : Rp{total_masuk:,}\n"
        f"💸 Keluar : Rp{total_keluar:,}\n"
        f"💵 Saldo : Rp{saldo_bulan:,}"
    )

# ==========================
# TOP PENGELUARAN
# ==========================

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = sheet.get_all_values()

    kategori_total = {}

    for row in data[1:]:

        try:

            if row[1] == "Keluar":

                kategori = row[4]
                nominal = int(row[2])

                kategori_total[kategori] = (
                    kategori_total.get(kategori, 0)
                    + nominal
                )

        except:
            pass

    if not kategori_total:

        await update.message.reply_text(
            "Belum ada data pengeluaran."
        )
        return

    hasil = sorted(
        kategori_total.items(),
        key=lambda x: x[1],
        reverse=True
    )

    pesan = "🏆 TOP PENGELUARAN\n\n"

    for kategori, nominal in hasil[:5]:

        pesan += (
            f"{kategori} : Rp{nominal:,}\n"
        )

    await update.message.reply_text(pesan)

# ==========================
# RINGKASAN HEMAT / BOROS
# ==========================

async def ringkasan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = sheet.get_all_values()

    masuk = 0
    keluar = 0

    for row in data[1:]:

        try:

            nominal = int(row[2])

            if row[1] == "Masuk":
                masuk += nominal

            elif row[1] == "Keluar":
                keluar += nominal

        except:
            pass

    if masuk == 0:

        await update.message.reply_text(
            "Belum ada data pemasukan."
        )
        return

    rasio = keluar / masuk

    if rasio > 0.8:
        status = "🔴 BOROS"

    elif rasio > 0.5:
        status = "🟡 NORMAL"

    else:
        status = "🟢 HEMAT"

    await update.message.reply_text(
        f"📈 RINGKASAN\n\n"
        f"Pengeluaran/Pemasukan : {rasio*100:.1f}%\n\n"
        f"Status : {status}"
    )

# ==========================
# BANTUAN
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Bot Keuangan\n\n"
        "Input:\n"
        "keluar 5000 kopi\n"
        "masuk 500000 gaji\n\n"
        "Perintah:\n"
        "/saldo\n"
        "/laporan\n"
        "/bulan\n"
        "/top\n"
        "/ringkasan"
    )

# ==========================
# MAIN
# ==========================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("laporan", laporan))
    app.add_handler(CommandHandler("bulan", bulan))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("ringkasan", ringkasan))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            simpan
        )
    )

    print("Bot aktif...")

    app.run_polling()

if __name__ == "__main__":
    main()