# Sintaks pencarian

SearXNG mempunyai sintaks pencarian memungkinkan Anda untuk mengubah kategori,
mesin pencari, bahasa dan lainnya.  Lihat {{link('preferensi', 'preferences')}} untuk
daftar mesin pencari, kategori dan bahasa.

## `!` pilih mesin pencari dan kategori

Untuk menetapkan nama kategori dan/atau mesin pencari gunakan awalan `!`.  Sebagai contoh:

- cari di Wikipedia tentang **Jakarta**

  - {{search('!wp Jakarta')}}
  - {{search('!wikipedia Jakarta')}}

- cari dalam kategori **peta** untuk **Jakarta**

  - {{search('!map Jakarta')}}

- pencarian gambar

  - {{search('!images kucing')}}

Singkatan mesin pencari dan bahasa juga diterima.  Pengubah
mesin/kategori dapat dirantai dan inklusif.  Misalnya dengan pencarian {{search('!map !ddg !wp
Jakarta')}} dalam kategori peta dan DuckDuckGo dan Wikipedia tentang **Jakarta**.

## `:` pilih bahasa

Untuk memilih saringan bahasa gunakan awalan `:`.  Sebagai contoh:

- cari Wikipedia dengan bahasa lain

  - {{search(':en !wp Jakarta')}}

## `!!` mesin pencarian (*bangs*) eksternal

SearXNG mendukung mesin pencarian eksternal (*bangs*) dari [DuckDuckGo].  Untuk langsung lompat ke sebuah
laman pencarian eksternal gunakan awalan `!!`.  Sebagai contoh:

- cari Wikipedia dengan bahasa yang lain

  - {{search('!!wen cat')}}

Diingat, pencarian Anda akan dilakukan secara langsung di mesin pencari eksternal,
SearXNG tidak dapat melindungi privasi Anda di sana.

[DuckDuckGo]: https://duckduckgo.com/bang

## Kueri Khusus

Dalam laman {{link('preferensi', 'preferences')}} Anda akan menemukan kata kunci
_kueri khusus_.  Sebagai contoh:

- buat sebuah UUID acak

  - {{search('random uuid')}}

- temukan rata-rata

  - {{search('avg 123 548 2.04 24.2')}}

- tampilkan _user agent_ (agen pengguna) dari peramban Anda (harus diaktifkan)

  - {{search('user-agent')}}

- ubah _string_ (teks) ke intisari *hash* yang berbeda (harus diaktifkan)

  - {{search('md5 kucing sphynx')}}
  - {{search('sha512 kucing sphynx')}}
