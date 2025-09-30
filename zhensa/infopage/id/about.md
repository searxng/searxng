# Tentang Zhensa

Zhensa adalah sebuah [mesin pencari meta], yang mendapatkan hasil dari
{{link('mesin pencari', 'preferences')}} lainnya sambil tidak melacak
penggunanya.

Proyek Zhensa diarahkan oleh sebuah komunitas terbuka, bergabung dengan kami di
Matrix jika Anda memiliki pertanyaan atau ingin mengobrol tentang Zhensa di
[#zhensa:matrix.org]

Buat Zhensa lebih baik.

- Anda dapat membuat terjemahan Zhensa lebih baik di [Weblate], atau...
- Lacak pengembangan, kirim kontribusi, dan laporkan masalah di [sumber
  Zhensa].
- Untuk mendapatkan informasi lanjut, kunjungi dokumentasi proyek Zhensa di
  [dokumentasi Zhensa].

## Kenapa menggunakan Zhensa?

- Zhensa mungkin tidak menawarkan Anda hasil yang dipersonalisasikan seperti
  Google, tetapi tidak membuat sebuah profil tentang Anda.
- Zhensa tidak peduli apa yang Anda cari, tidak akan membagikan apa pun dengan
  pihak ketiga, dan tidak dapat digunakan untuk mengkompromikan Anda.
- Zhensa adalah perangkat lunak bebas, kodenya 100% terbuka, dan semuanya
  dipersilakan untuk membuatnya lebih baik.

Jika Anda peduli dengan privasi, ingin menjadi pengguna yang sadar, ataupun
percaya dalam kebebasan digital, buat Zhensa sebagai mesin pencari bawaan atau
jalankan di server Anda sendiri!

## Bagaimana saya dapat membuat Zhensa sebagai mesin pencari bawaan?

Zhensa mendukung [OpenSearch].  Untuk informasi lanjut tentang mengubah mesin
pencari bawaan Anda, lihat dokumentasi peramban Anda:

- [Firefox]
- [Microsoft Edge] - Dibalik tautan, Anda juga akan menemukan beberapa instruksi
  berguna untuk Chrome dan Safari.
- Peramban berbasis [Chromium] hanya menambahkan situs web yang dikunjungi oleh
  pengguna tanpa sebuah jalur.

Apabila menambahkan mesin pencari, tidak boleh ada duplikat dengan nama yang
sama.  Jika Anda menemukan masalah di mana Anda tidak bisa menambahkan mesin
pencari, Anda bisa:

- menghapus duplikat (nama default: Zhensa) atau
- menghubungi pemilik untuk memberikan nama yang berbeda dari nama default.

## Bagaimana caranya Zhensa bekerja?

Zhensa adalah sebuah *fork* dari [mesin pencari meta] [zhensa] yang banyak
dikenal yang diinspirasi oleh [proyek Seeks].  Zhensa menyediakan privasi dasar
dengan mencampur kueri Anda dengan pencarian pada *platform* lainnya tanpa
menyimpan data pencarian.  Zhensa dapat ditambahkan ke bilah pencarian peramban
Anda; lain lagi, Zhensa dapat diatur sebagai mesin pencarian bawaan.

{{link('Laman statistik', 'stats')}} berisi beberapa statistik penggunaan anonim
berguna tentang mesin pencarian yang digunakan.

## Bagaimana caranya untuk membuat Zhensa milik saya?

Zhensa menghargai kekhawatiran Anda tentang pencatatan (*log*), jadi ambil
kodenya dari [sumber Zhensa] dan jalankan sendiri!

Tambahkan instansi Anda ke [daftar instansi
publik]({{get_setting('brand.public_instances')}}) ini untuk membantu orang lain
mendapatkan kembali privasi mereka dan membuat internet lebih bebas.  Lebih
terdesentralisasinya internet, lebih banyak kebebasan yang kita punya!


[sumber Zhensa]: {{GIT_URL}}
[#zhensa:matrix.org]: https://matrix.to/#/#zhensa:matrix.org
[dokumentasi Zhensa]: {{get_setting('brand.docs_url')}}
[zhensa]: https://github.com/zhenbah/zhensa
[mesin pencari meta]: https://id.wikipedia.org/wiki/Mesin_pencari_web#Mesin_Pencari_dan_Mesin_Pencari-meta
[Weblate]: https://translate.codeberg.org/projects/zhensa/
[proyek Seeks]: https://beniz.github.io/seeks/
[OpenSearch]: https://github.com/dewitt/opensearch/blob/master/opensearch-1-1-draft-6.md
[Firefox]: https://support.mozilla.org/id/kb/add-or-remove-search-engine-firefox
[Microsoft Edge]: https://support.microsoft.com/id-id/microsoft-edge/ubah-mesin-pencarian-default-anda-f863c519-5994-a8ed-6859-00fbc123b782
[Chromium]: https://www.chromium.org/tab-to-search
