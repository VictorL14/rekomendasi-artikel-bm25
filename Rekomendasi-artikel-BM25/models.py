from config import *
from collections import Counter
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import os
import pandas as pd
import pdfplumber
import string
import nltk
import numpy as np
from collections import Counter          
            
def get_pengguna_id(npm):
    """Get pengguna_id based on npm."""
    conn = create_connection()
    pengguna_id = None
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM pengguna WHERE npm = %s", (npm,))
            result = cursor.fetchone()
            if result:
                pengguna_id = result[0]
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
        finally:
            close_connection(conn)
    return pengguna_id
        


#ARTIKEL   
#FILE PATH
def upload_file(nama_path):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO file_path (nama_file) VALUES (%s)", (nama_path))
            conn.commit()
            print("Berhasil menambah file")
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
        finally:
            close_connection(conn)

def create_url_from_title(title):
    # Mengubah judul menjadi huruf kecil dan mengganti spasi dengan tanda hubung
    return title.lower().replace(' ', '-')


def lihat_hasil_rekom(pengguna_id):
    conn = create_connection()
    melihat_rekom = []
    if conn:
        cursor = conn.cursor()
        try:
            query = """
            SELECT artikel.judul_awal FROM kueri
            JOIN artikel ON kueri.artikel_id = artikel.id
            JOIN pengguna ON kueri.pengguna_id = pengguna.id
            WHERE pengguna_id = %s
            """
            cursor.execute(query, (pengguna_id))
            melihat_rekom = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
        finally:
            close_connection(conn)
    return melihat_rekom


def preprocess_text(text):
    # 1. Case Folding
    text = text.lower()

    # 2. Tokenizing
    tokens = word_tokenize(text)

    # 3. Filtering Stopwords
    stop_words = set(stopwords.words('indonesian'))
    tokens = [word for word in tokens if word.lower() not in stop_words]

    # 4. Stemming
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    tokens = [stemmer.stem(word) for word in tokens]

    # Menggabungkan tokens kembali menjadi teks
    preprocessed_text = ' '.join(tokens)

    return preprocessed_text

def extract_abstract(pdf_file_path):
    with pdfplumber.open(pdf_file_path) as pdf:
        # Tambahkan teks dari halaman kedua
        second_page_text = pdf.pages[1].extract_text()
        second_page_text_lines = second_page_text.split('\n')
        second_page_text = '\n'.join(second_page_text_lines[2:])

        # Pendeteksian untuk mengecek apakah ada kop halaman atau nomor halaman pada baris terakhir halaman pertama
        first_page_text = pdf.pages[0].extract_text()
        first_page_text_lines = first_page_text.split('\n')
        # Hapus baris terakhir pada halaman pertama
        first_page_text = '\n'.join(first_page_text_lines[:-1])

        # Gabungkan teks dari kedua halaman
        combined_text = first_page_text + '\n' + second_page_text

        # Cari abstrak dalam bahasa Indonesia
        abstract_match = re.search(r'(?<=\bABSTRAK\b).*?\b(Kata\s?[kK]unci)', combined_text, re.DOTALL)
        abstract = abstract_match.group(0).strip() if abstract_match else ''

        # Bersihkan karakter '\n' dan '\r'
        abstract = abstract.replace('\n', ' ').replace('\r', '')

        # Hilangkan kata kunci dari abstrak
        abstract = re.sub(r'\b(Kata\s?[kK]unci)\b', '', abstract)

        # Preprocessing teks abstrak
        abstract = preprocess_text(abstract)

        return abstract
    
def extract_raw_title_from_pdf(pdf_file_path):
    raw_title = ""
    with pdfplumber.open(pdf_file_path) as pdf:
        first_page = pdf.pages[0]
        first_page_text = first_page.extract_text()

        # Ambil baris-baris dari halaman pertama
        lines = first_page_text.split('\n')

        # Flag untuk menunjukkan apakah kata dengan angka 1 tanpa spasi telah ditemukan
        found_flag = False

        # Ambil baris-baris yang memenuhi kriteria
        title_lines = []
        for line in lines:
            stripped_line = line.strip()

            # Cek apakah baris mengandung kata dengan angka 1 tanpa spasi
            if re.search(r'\b\w*1,|2,|1 ,|1\*|Institut|Universitas|[A-Za-z]+\d(?:,|\s*,|\s*\*,)?\w*\b', stripped_line):
                found_flag = True

            # Tambahkan baris ke dalam judul selama flag belum ditemukan
            if not found_flag:
                title_lines.append(stripped_line)

        # Gabungkan baris-baris menjadi satu teks
        raw_title = ' '.join(title_lines)

    return raw_title

def extract_title_from_pdf(pdf_file_path):
    title = ""
    with pdfplumber.open(pdf_file_path) as pdf:
        first_page = pdf.pages[0]
        first_page_text = first_page.extract_text()

        # Ambil baris-baris dari halaman pertama
        lines = first_page_text.split('\n')

        # Flag untuk menunjukkan apakah kata dengan angka 1 tanpa spasi telah ditemukan
        found_flag = False

        # Ambil baris-baris yang memenuhi kriteria
        title_lines = []
        for line in lines:
            stripped_line = line.strip()

            # Cek apakah baris mengandung kata dengan angka 1 tanpa spasi
            if re.search(r'\b\w*1,|2,|1 ,|1\*|Institut|Universitas|[A-Za-z]+\d(?:,|\s*,|\s*\*,)?\w*\b', stripped_line):
                found_flag = True

            # Tambahkan baris ke dalam judul selama flag belum ditemukan
            if not found_flag:
                title_lines.append(stripped_line)

        # Gabungkan baris-baris menjadi satu teks
        title = ' '.join(title_lines)

        # Preprocessing teks judul
        title = preprocess_text(title)

    return title


def extract_year(text):
    # Mencari tahun dalam format XXXX (misalnya: 2022)
    match = re.search(r'\b\d{4}\b', text)

    return int(match.group()) if match else None


def extract_year_from_pdf(pdf_file_path):
    with pdfplumber.open(pdf_file_path) as pdf:
        # Tambahkan teks dari baris pertama halaman kedua
        second_page_text = pdf.pages[1].extract_text()
        first_line_second_page = second_page_text.split('\n')[0]

        # Cari tahun dalam teks pada baris pertama halaman kedua
        year = extract_year(first_line_second_page)

        return year


def extract_authors_from_pdf(pdf_file_path):
    with pdfplumber.open(pdf_file_path) as pdf:
        first_page = pdf.pages[0]
        first_page_text = first_page.extract_text()

        # Ambil baris-baris dari halaman pertama
        lines = first_page_text.split('\n')

        # Variabel untuk menyimpan baris yang mengandung nama penulis
        authors_line = ""

        # Flag untuk menunjukkan apakah kata "universitas" atau "institut" ditemukan
        institute_flag = False

        # Loop melalui setiap baris dalam teks
        for line in lines:
            stripped_line = line.strip()

            # Cek apakah baris mengandung kata "universitas" atau "institut"
            if re.search(r'\b(Institut|Universitas|Jurusan|Teknik)\b', stripped_line):
                institute_flag = True

            # Cek apakah baris mengandung pola nama dengan angka yang tidak berurutan
            # atau angka 1 atau 2 diikuti oleh koma tanpa spasi
            if re.search(r'\b[A-Za-z]+\d(?:,|\s*,| \d*,|\s*\*,)', stripped_line) and not institute_flag:
                authors_line = stripped_line
                break

        # Bersihkan spasi di sekitar nama penulis
        cleaned_authors = [author.strip() for author in authors_line.split(',')]

    return cleaned_authors

#r'\b[A-Za-z]+\d(?:,|\s*,| \d*,|\s*\*,)'
# Fungsi untuk menjalani folder
def process_folders_in_directory(folder_path):
    pdf_info = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_file_path = os.path.join(root, file)
                abstract = extract_abstract(pdf_file_path)
                title = extract_title_from_pdf(pdf_file_path)
                
                raw_title = extract_raw_title_from_pdf(pdf_file_path)
                
                # Tambahan: ekstrak tahun dari PDF
                year = extract_year_from_pdf(pdf_file_path)

                # Ekstrak nama penulis dari judul artikel
                authors = extract_authors_from_pdf(pdf_file_path)

                # Rename the file by removing '.pdf' extension
                

                pdf_info.append((raw_title, title, abstract, year, authors))
                af = pd.DataFrame(pdf_info, columns=['judul_awal','judul', 'abstrak', 'tahun', 'nama_penulis'])
    return af

#KUERI
def tambah_kueri(pengguna_id, kueri):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO kueri (pengguna_id, kueri) VALUES (%s, %s)", (pengguna_id, kueri))
            conn.commit()
            print("kueri berhasail ditambah")
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
        finally:
            close_connection(conn)
            
            
def lihat_kueri(): #untuk sisi admin
    conn = create_connection()
    melihat_kueri = []
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM kueri")
            melihat_kueri = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
        finally:
            close_connection(conn)
    return melihat_kueri


#=======PREPROCESSSING========
#QUERY
def preprocess_query(query):
    # 1. Case Folding
    query = query.lower()

    # 2. Tokenizing
    tokens = word_tokenize(query)

    # 3. Filtering Stopwords (Opsional)
    stop_words = set(stopwords.words('indonesian'))
    tokens = [word for word in tokens if word.lower() not in stop_words]

    # 4. Stemming (Opsional)
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    tokens = [stemmer.stem(word) for word in tokens]

    # Menggabungkan tokens kembali menjadi teks
    preprocessed_query = ' '.join(tokens)

    return preprocessed_query

#=============================================================
def calculate_idf(documents):
    # Inisialisasi objek TfidfVectorizer
    tfidf_vectorizer = TfidfVectorizer()

    # Melakukan transformasi TF-IDF pada dokumen
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents)

    # Mendapatkan nama fitur (kata) dari vektorizer
    feature_names = tfidf_vectorizer.get_feature_names_out()

    # Menghitung N (jumlah dokumen dalam korpus)
    N = tfidf_matrix.shape[0]

    # Menghitung df(qi) (frekuensi dokumen yang mengandung term qi)
    df_qi = np.array([(tfidf_matrix[:, i] > 0).sum() for i in range(tfidf_matrix.shape[1])])

    # Menghitung IDF menggunakan rumus yang diberikan
    idf_values = np.log((N - df_qi + 0.5) / (df_qi + 0.5))

    # Menyusun hasil ke dalam dictionary
    idf_dict = {feature_names[i]: idf_values[i] for i in range(len(feature_names))}

    return idf_dict

def calculate_term_frequency(documents):
    term_document_matrix = {}
    terms = set()

    # Hitung frekuensi term dan term tersebut termasuk dalam dokumen mana
    for doc_id, document in enumerate(documents):
        terms_in_document = set(document.split())
        for term in terms_in_document:
            if term not in term_document_matrix:
                term_document_matrix[term] = {}
            term_document_matrix[term][doc_id] = document.count(term)
            terms.add(term)

    # Menyusun hasil ke dalam dictionary
    term_frequency_dict = {}
    for term in terms:
        term_frequency_dict[term] = [term_document_matrix.get(term, {}).get(doc_id, 0) for doc_id in range(len(documents))]

    return term_frequency_dict



#JUDUL
def calculate_bm25_judul(processed_query, af, k1, b):
    # Hitung IDF dan term frequency
    word_freq = Counter(af['judul'].str.split().explode().dropna())
    idf_teks = calculate_idf(af['judul'])
    tfd = calculate_term_frequency(af['judul'])
    avg_dl_teks = sum(len(teks.split()) for teks in af['judul']) / len(af) 
    bm25_scores = {}  # Inisialisasi kamus BM25

    for i, teks in enumerate(af['judul']):
        bm25_judul = 0
        # Hitung panjang judul dari dokumen saat ini
        panjang_judul = len(teks.split())
        panjang_judul_dibagi_avg_dl = panjang_judul / avg_dl_teks
        for term in processed_query.split():
            if term in tfd and term in idf_teks:
                tf = tfd[term][i]  # Frekuensi term di dalam judul, default 0 jika tidak ada
                tf_array = np.array(tf)
                idf = idf_teks[term]  # IDF dari term, default 0 jika tidak ada
                bm25_judul += idf * (tf_array * (k1 + 1)) / (tf_array + (k1 * (1 - b + b)) * (panjang_judul_dibagi_avg_dl))
        bm25_scores[i] = bm25_judul  # Menambahkan skor BM25 ke dalam kamus
    
    return bm25_scores  # Mengembalikan kamus BM25

#abstrak
def calculate_bm25_abstrak(processed_query, af, k1, b):
    # Hitung IDF dan term frequency
    word_freq = Counter(af['abstrak'].str.split().explode().dropna())
    idf_teks = calculate_idf(af['abstrak'])
    tfd = calculate_term_frequency(af['abstrak'])
    avg_dl_teks = sum(len(teks.split()) for teks in af['abstrak']) / len(af) 
    bm25_scores = {}  # Inisialisasi kamus BM25

    for i, teks in enumerate(af['abstrak']):
        bm25_abstrak = 0
        # Hitung panjang abstrak dari dokumen saat ini
        panjang_abstrak = len(teks.split())
        panjang_abstrak_dibagi_avg_dl = panjang_abstrak / avg_dl_teks
        for term in processed_query.split():
            if term in tfd and term in idf_teks:
                tf = tfd[term][i]  # Frekuensi term di dalam abstrak, default 0 jika tidak ada
                tf_array = np.array(tf)
                idf = idf_teks[term]  # IDF dari term, default 0 jika tidak ada
                bm25_abstrak += idf * (tf_array * (k1 + 1)) / (tf_array + (k1 * (1 - b + b)) * (panjang_abstrak_dibagi_avg_dl))
        bm25_scores[i] = bm25_abstrak  # Menambahkan skor BM25 ke dalam kamus
    
    return bm25_scores  # Mengembalikan kamus BM25

#GABUNGAN JUDUL DAN abstrak
def calculate_bm25_judul_abstrak(processed_query, af, k1 ,b):
    judul_abstrak = af['judul'] + ' ' + af['abstrak']
    # Hitung IDF dan term frequency untuk judul
    word_freq = Counter(judul_abstrak.str.split().explode().dropna())
    idf_teks = calculate_idf(judul_abstrak)
    tfd = calculate_term_frequency(judul_abstrak)
    avg_dl_teks = sum(len(teks.split()) for teks in judul_abstrak) / len(af) 
    bm25_scores = {}  # Inisialisasi kamus BM25

    for i, teks in enumerate(judul_abstrak):
        bm25_judul_abstrak = 0
        # Hitung panjang judul_abstrak dari dokumen saat ini
        panjang_judul_abstrak = len(teks.split())
        panjang_judul_abstrak_dibagi_avg_dl = panjang_judul_abstrak / avg_dl_teks
        for term in processed_query.split():
            if term in tfd and term in idf_teks:
                tf = tfd[term][i]  # Frekuensi term di dalam judul_abstrak, default 0 jika tidak ada
                tf_array = np.array(tf)
                idf = idf_teks[term]  # IDF dari term, default 0 jika tidak ada
                bm25_judul_abstrak += idf * (tf_array * (k1 + 1)) / (tf_array + (k1 * (1 - b + b)) * (panjang_judul_abstrak_dibagi_avg_dl))
        bm25_scores[i] = bm25_judul_abstrak  # Menambahkan skor BM25 ke dalam kamus
    
    return bm25_scores  # Mengembalikan kamus BM25







#==============================================================










# #MENGHITUNG IDF
# def calculate_idf(texts):
#     total_docs = len(texts)
#     term_doc_occurrences = Counter(word for text in texts for word in set(text.split()))
#     return {term: np.log((total_docs - count + 0.5) / (count + 0.5) + 1) for term, count in term_doc_occurrences.items()}

# #MENGHITUNG TF
# def calculate_term_frequency(texts):
#     tf = {}
#     for doc_id, text in enumerate(texts):
#         for word in text.split():
#             if word not in tf:
#                 tf[word] = [0] * len(texts)
#             tf[word][doc_id] += 1
#     return tf

# #=====RANKBM25======
# #JUDUL
# def calculate_bm25_judul(processed_query, articles, k1, b):
#     judul = [article['judul'] for article in articles]
#     word_freq = Counter(word for text in judul for word in text.split())
#     idf_teks = calculate_idf(judul)
#     tfd = calculate_term_frequency(judul)
#     avg_dl_teks = sum(len(text.split()) for text in judul) / len(judul)
#     bm25_scores = {}

#     for i, text in enumerate(judul):
#         bm25_judul = 0
#         panjang_judul = len(text.split())
#         panjang_judul_dibagi_avg_dl = panjang_judul / avg_dl_teks
#         for term in processed_query.split():
#             if term in tfd and term in idf_teks:
#                 tf = tfd[term][i]
#                 tf_array = np.array(tf)
#                 idf = idf_teks[term]
#                 bm25_judul += idf * (tf_array * (k1 + 1)) / (tf_array + (k1 * (1 - b + b)) * panjang_judul_dibagi_avg_dl)
#         bm25_scores[i] = bm25_judul

#     return bm25_scores

# #ABSTRAK
# def calculate_bm25_abstrak(processed_query, articles, k1, b):
#     abstracts = [article['abstrak'] for article in articles]
#     word_freq = Counter(word for text in abstracts for word in text.split())
#     idf_teks = calculate_idf(abstracts)
#     tfd = calculate_term_frequency(abstracts)
#     avg_dl_teks = sum(len(text.split()) for text in abstracts) / len(abstracts)
#     bm25_scores = {}

#     for i, text in enumerate(abstracts):
#         bm25_abstrak = 0
#         panjang_abstrak = len(text.split())
#         panjang_abstrak_dibagi_avg_dl = panjang_abstrak / avg_dl_teks
#         for term in processed_query.split():
#             if term in tfd and term in idf_teks:
#                 tf = tfd[term][i]
#                 tf_array = np.array(tf)
#                 idf = idf_teks[term]
#                 bm25_abstrak += idf * (tf_array * (k1 + 1)) / (tf_array + (k1 * (1 - b + b)) * panjang_abstrak_dibagi_avg_dl)
#         bm25_scores[i] = bm25_abstrak

#     return bm25_scores


# #GABUNGAN
# def calculate_bm25_gabungan(processed_query, articles, k1, b):
#     gabungan = [article['judul'] + " " + article['abstrak'] for article in articles]
    
#     # Hitung IDF dan term frequency untuk teks gabungan
#     idf_teks = calculate_idf(gabungan)
#     tfd = calculate_term_frequency(gabungan)
    
#     avg_dl_teks = sum(len(teks.split()) for teks in gabungan) / len(gabungan)
#     bm25_scores = {}

#     for i, teks in enumerate(gabungan):
#         bm25_gabungan = 0
#         panjang_teks = len(teks.split())
#         panjang_teks_dibagi_avg_dl = panjang_teks / avg_dl_teks
#         for term in processed_query.split():
#             if term in tfd and term in idf_teks:
#                 tf = tfd[term][i]  # Frekuensi term di dalam teks gabungan
#                 tf_array = np.array(tf)
#                 idf = idf_teks[term]  # IDF dari term
#                 bm25_gabungan += idf * (tf_array * (k1 + 1)) / (tf_array + (k1 * (1 - b + b)) * (panjang_teks_dibagi_avg_dl))
#         bm25_scores[i] = bm25_gabungan
    
#     return bm25_scores