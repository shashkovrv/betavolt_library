"""
Скрипт загрузки и каталогизации полнотекстовых PDF-документов научной литературы проекта.
Самарский государственный технический университет (СамГТУ)
"""

import os
import shutil
import ssl
import sys
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CTX = ssl._create_unverified_context()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

LIT_DIR = Path("D:/project_betavolt/literature")
PDF_DIR = LIT_DIR / "pdf"
PDF_DIR.mkdir(parents=True, exist_ok=True)

REF_DIR = Path("D:/betavolt-screening/betavolt-screening/docs/literature")

# Список целевых документов для загрузки и размещения
DOWNLOAD_TARGETS = [
    # 1. Фундаментальные физические стандарты и константы
    {
        "filename": "00_CODATA_2022_Fundamental_Physical_Constants.pdf",
        "title": "CODATA Recommended Values of the Fundamental Physical Constants: 2022",
        "authors": "Tiesinga E., Mohr P. J., Newell D. B., Taylor B. N.",
        "year": 2024,
        "ref_source": "01_CODATA_2022_Fundamental_Physical_Constants.pdf",
        "urls": [
            "https://physics.nist.gov/cuu/pdf/sp961.pdf",
            "https://arxiv.org/pdf/2405.15838.pdf"
        ]
    },
    {
        "filename": "00_NIST_ESTAR_Stopping_Power_and_Range_Tables.pdf",
        "title": "ESTAR, PSTAR, and ASTAR: Stopping-Power and Range Tables for Electrons",
        "authors": "Berger M. J., Coursey J. S., Zucker M. A., Chang J.",
        "year": 2005,
        "ref_source": "02_NIST_ESTAR_Stopping_Power_and_Range_Tables.pdf",
        "urls": [
            "https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir4999.pdf"
        ]
    },
    # 2. Квантово-машинное обучение (Delta-Learning)
    {
        "filename": "07_Ramakrishnan_2015_Delta_Machine_Learning.pdf",
        "title": "Big Data Meets Quantum Chemistry Approximations: The Delta-Machine Learning Approach",
        "authors": "Ramakrishnan R., Dral P. O., Rupp M., von Lilienfeld O. A.",
        "year": 2015,
        "ref_source": "22_Ramakrishnan_2015_Big_Data_Quantum_Chemistry_Delta_Learning.pdf",
        "urls": [
            "https://arxiv.org/pdf/1503.04987.pdf"
        ]
    },
    # 3. Materials Project
    {
        "filename": "08_Jain_2013_The_Materials_Project.pdf",
        "title": "The Materials Project: A materials genome approach to accelerating materials innovation",
        "authors": "Jain A., Ong S. P., Hautier G., Ceder G., Persson K. A. et al.",
        "year": 2013,
        "ref_source": "23_Jain_2013_The_Materials_Project.pdf",
        "urls": [
            "https://pubs.aip.org/aip/apm/article-pdf/doi/10.1063/1.4812323/13164983/011002_1_online.pdf"
        ]
    },
    # 4. Бенчмарк Matbench
    {
        "filename": "09_Dunn_2020_Matbench_Benchmark.pdf",
        "title": "Benchmarking materials property prediction methods: the Matbench test set",
        "authors": "Dunn A., Wang Q., Ganose A., Dopp D., Jain A.",
        "year": 2020,
        "ref_source": "24_Dunn_2020_Matbench_Benchmark.pdf",
        "urls": [
            "https://www.nature.com/articles/s41524-020-00406-3.pdf",
            "https://arxiv.org/pdf/2005.03607.pdf"
        ]
    },
    # 5. Аналитический обзор Deep Learning и ML в материаловедении
    {
        "filename": "10_Choudhary_2022_Deep_Learning_Materials_Science.pdf",
        "title": "Recent advances and applications of deep learning and machine learning in materials science",
        "authors": "Choudhary K., DeCost B., Chen C., Jain A. et al.",
        "year": 2022,
        "ref_source": "32_Choudhary_2022_Deep_Learning_Materials_Science.pdf",
        "urls": [
            "https://www.nature.com/articles/s41524-022-00734-6.pdf",
            "https://arxiv.org/pdf/2111.05943.pdf"
        ]
    },
    # 6. Алгоритм градиентного бустинга CatBoost
    {
        "filename": "11_Prokhorenkova_2018_CatBoost.pdf",
        "title": "CatBoost: unbiased boosting with categorical features",
        "authors": "Prokhorenkova L., Gusev G., Vorobev A., Dorogush A., Gulin A.",
        "year": 2018,
        "ref_source": "26_Prokhorenkova_2018_CatBoost.pdf",
        "urls": [
            "https://proceedings.neurips.cc/paper/2018/file/14491b756b3a51daac41c24863285549-Paper.pdf",
            "https://arxiv.org/pdf/1706.09516.pdf"
        ]
    },
    # 7. Дескрипторы состава Magpie
    {
        "filename": "00_Ward_2016_Magpie_Framework.pdf",
        "title": "A general-purpose machine learning framework for predicting properties of inorganic materials",
        "authors": "Ward L., Agrawal A., Choudhary C., Wolverton C.",
        "year": 2016,
        "ref_source": "25_Ward_2016_Magpie_Framework.pdf",
        "urls": [
            "https://www.nature.com/articles/npjcompumats201628.pdf",
            "https://arxiv.org/pdf/1604.05318.pdf"
        ]
    },
    # 8. Olsen - Фундаментальный обзор теории бетавольтаики (NASA NTRS STI Archive)
    {
        "filename": "05_Olsen_1994_NASA_Review_of_Betavoltaic_Energy_Conversion.pdf",
        "title": "Review of Betavoltaic Energy Conversion",
        "authors": "Olsen L. C. (NASA Lewis Research Center)",
        "year": 1994,
        "ref_source": None,
        "urls": [
            "https://ntrs.nasa.gov/api/citations/19940006935/downloads/19940006935.pdf"
        ]
    },
    # 9. Преобразование энергии в GaP бетавольтаических ячейках (NASA NTRS STI)
    {
        "filename": "00_Olsen_1995_NASA_GaP_Power_Conversion_Betavoltaic.pdf",
        "title": "High efficiency GaP power conversion for Betavoltaic applications",
        "authors": "Olsen L. C. et al. (NASA STI)",
        "year": 1995,
        "ref_source": None,
        "urls": [
            "https://ntrs.nasa.gov/api/citations/19950014124/downloads/19950014124.pdf"
        ]
    },
    # 10. Современное исследование бетавольтаических полупроводников (arXiv:2308.09807)
    {
        "filename": "00_Arias_2023_Theoretical_Study_Betavoltaic_Transducers.pdf",
        "title": "Theoretical study of conventional semiconductors as transducers to increase power and efficiency in betavoltaic batteries",
        "authors": "Arias C. A., Morales-Acevedo A. et al.",
        "year": 2023,
        "ref_source": None,
        "urls": [
            "https://arxiv.org/pdf/2308.09807.pdf"
        ]
    },
    # 11. Моделирование источника Ni-63 (arXiv:1903.09098)
    {
        "filename": "00_Hossain_2019_Model_Ni63_Source_Betavoltaic.pdf",
        "title": "A model for Ni-63 source for betavoltaic application",
        "authors": "Hossain M. S. et al.",
        "year": 2019,
        "ref_source": None,
        "urls": [
            "https://arxiv.org/pdf/1903.09098.pdf"
        ]
    },
    # 12. Анализ КПД прямозонных бетавольтаических ячеек (arXiv:1504.03179)
    {
        "filename": "00_Khadir_2015_Attainable_Efficiency_Direct_Bandgap_Betavoltaic.pdf",
        "title": "Analysis of the attainable efficiency of a direct-bandgap betavoltaic element",
        "authors": "Khadir S. et al.",
        "year": 2015,
        "ref_source": None,
        "urls": [
            "https://arxiv.org/pdf/1504.03179.pdf"
        ]
    },
    # 13. Анализ предельного КПД бетавольтаики (arXiv:1412.7826)
    {
        "filename": "00_Sanami_2014_Efficiency_Analysis_Betavoltaic_Elements.pdf",
        "title": "Efficiency analysis of betavoltaic elements",
        "authors": "Sanami S. et al.",
        "year": 2014,
        "ref_source": None,
        "urls": [
            "https://arxiv.org/pdf/1412.7826.pdf"
        ]
    }
]


def is_valid_pdf(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1024:
        return False
    try:
        with open(path, "rb") as f:
            header = f.read(5)
            return header.startswith(b"%PDF")
    except Exception:
        return False


def fetch_pdf(url: str, dest_path: Path, timeout: int = 15) -> bool:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as response:
            content = response.read()
            if content.startswith(b"%PDF"):
                with open(dest_path, "wb") as f:
                    f.write(content)
                return True
    except Exception as e:
        # print(f"    [!] Ошибка загрузки с {url[:60]}: {e}")
        pass
    return False


def main():
    print(f"[*] Начало загрузки и проверки PDF литературы в папку: {PDF_DIR}\n", flush=True)

    results = []

    for item in DOWNLOAD_TARGETS:
        fname = item["filename"]
        target = PDF_DIR / fname
        title = item["title"]

        print(f"[*] Обработка: {fname} ({title[:50]}...)", flush=True)

        # 1. Проверяем, существует ли уже корректный PDF
        if is_valid_pdf(target):
            size_mb = target.stat().st_size / (1024 * 1024)
            print(f"  -> Уже загружен ({size_mb:.2f} МБ)", flush=True)
            results.append({"item": item, "status": "Ready", "size_mb": size_mb, "path": target})
            continue

        # 2. Если есть референсный файл из мастер-коллекции, копируем его
        copied = False
        if item.get("ref_source"):
            ref_path = REF_DIR / item["ref_source"]
            if is_valid_pdf(ref_path):
                shutil.copy2(ref_path, target)
                if is_valid_pdf(target):
                    size_mb = target.stat().st_size / (1024 * 1024)
                    print(f"  [OK] Синхронизирован из эталонной коллекции ({size_mb:.2f} МБ)", flush=True)
                    results.append({"item": item, "status": "Ready", "size_mb": size_mb, "path": target})
                    copied = True

        if copied:
            continue

        # 3. Загружаем из сети
        downloaded = False
        for url in item.get("urls", []):
            print(f"  -> Загрузка из открытого репозитория: {url[:70]}...", flush=True)
            if fetch_pdf(url, target):
                if is_valid_pdf(target):
                    size_mb = target.stat().st_size / (1024 * 1024)
                    print(f"  [OK] Успешно загружен ({size_mb:.2f} МБ)", flush=True)
                    results.append({"item": item, "status": "Ready", "size_mb": size_mb, "path": target})
                    downloaded = True
                    break
                else:
                    if target.exists():
                        target.unlink()

        if not downloaded:
            print(f"  [!] Требуется авторизованный библиотечный доступ (ScienceDirect/Springer/IEEE/РИНЦ)", flush=True)
            results.append({"item": item, "status": "Paywalled", "size_mb": 0, "path": None})

    # Создание детального отчета PDF_INDEX.md
    index_path = LIT_DIR / "PDF_INDEX.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# 📑 Каталог полнотекстовых PDF-документов научной литературы\n\n")
        f.write("> **Организация:** Самарский государственный технический университет (СамГТУ)  \n")
        f.write("> **Тема ВКР:** «Машинное обучение и компьютерное моделирование в скрининге бетавольтаических полупроводников»  \n")
        f.write(f"> **Директория хранения PDF:** `literature/pdf/`  \n\n")
        f.write("---\n\n")
        f.write("### 📦 Реестр полнотекстовых файлов в проекте\n\n")
        f.write("| № | Файл PDF | Название работы | Авторы | Год | Размер | Статус |\n")
        f.write("|---|---|---|---|---|---|---|\n")

        idx = 1
        for res in results:
            it = res["item"]
            status_badge = f"✅ Готов ({res['size_mb']:.2f} МБ)" if res["status"] == "Ready" else "🔒 Закрытый доступ"
            file_link = f"[`{it['filename']}`](./pdf/{it['filename']})" if res["status"] == "Ready" else f"`{it['filename']}`"
            f.write(f"| {idx} | {file_link} | **{it['title']}** | {it['authors']} | {it['year']} | {res['size_mb']:.2f} МБ | {status_badge} |\n")
            idx += 1

        f.write("\n---\n\n")
        f.write("### 🌐 Инструкция по получению статей из закрытых академических баз\n\n")
        f.write("Ряд исторических и коммерческих публикаций (Elsevier, Springer, AIP, IEEE, РИНЦ/Наука) защищены авторским правом издательств. Для их загрузки рекомендуется использовать:\n")
        f.write("1. **Университетский прокси СамГТУ / elibrary.ru** — доступ к подписным базам журналов «Приборы и техника эксперимента» и «Физика и техника полупроводников»;\n")
        f.write("2. **ResearchGate / Авторские копии** — прямой запрос полнотекстовой копии у авторов (Бормашов В.С., Леготин С.А., Краснов А.А.);\n")
        f.write("3. **Открытые репозитории arXiv / NASA STI / NIST** — официальные препринты и государственные технические отчеты без пейволлов.\n")

    print("\n" + "=" * 60, flush=True)
    ready_count = sum(1 for r in results if r["status"] == "Ready")
    total_size_mb = sum(r["size_mb"] for r in results if r["status"] == "Ready")
    print(f"Готово! В папку literature/pdf/ успешно сохранено {ready_count} из {len(DOWNLOAD_TARGETS)} документов.", flush=True)
    print(f"Суммарный объем полнотекстовых PDF: {total_size_mb:.2f} МБ.", flush=True)
    print(f"Сформирован отчет: {index_path}", flush=True)


if __name__ == "__main__":
    main()
