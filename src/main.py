import urllib.request
import tarfile
import io
import sys
from typing import Optional, Dict, List
import sys


def get_args():
    """Проверка корректности аргументов"""
    argv = sys.argv
    if len(argv) > 4:
        try:
            if argv[4].lower() not in ["true", "false"]:
                raise ValueError
        except ValueError:
            print("[ERROR] Неправильный параметр режима работы с репозиторием")
    if len(argv) > 6:
        try:
            if argv[6].lower() not in ["true", "false"]:
                raise ValueError
        except ValueError:
            print("[ERROR] Неправильный параметр режима вывод зависимостей")
            return False
    return True

def download_apkindex(repo_url: str):
    """Скачивает APK файл"""
    if not repo_url.endswith("APKINDEX.tar.gz"):
        if not repo_url.endswith("/"):
            repo_url += "/"
        repo_url += "APKINDEX.tar.gz"

    print(f"[INFO] Загрузка индекса: {repo_url}")
    request = urllib.request.Request(
        repo_url,
        headers={"User-Agent": "AlpineDepsFetcher/1.0"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def extract_apkindex(archive_bytes: bytes):
    """Распаковывает APK файл и возвращает его содержимое"""
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.name in ("APKINDEX", "APKINDEX.tar.gz/APKINDEX"):
                f = tar.extractfile(member)
                if f is not None:
                    return f.read().decode("utf-8", errors="replace")
    raise RuntimeError("Файл APKINDEX не найден в архиве")


def parse_apkindex(content: str):
    """Парсит содержимое APK файла в список словарей"""
    packages: List[Dict[str, str]] = []
    current: Dict[str, str] = {}

    for raw_line in content.splitlines():
        line = raw_line.rstrip("\n")
        if not line:
            if current:
                packages.append(current)
                current = {}
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        if key in current:
            current[key] = current[key] + " " + value
        else:
            current[key] = value

    if current:
        packages.append(current)
    return packages


def find_package(packages: List[Dict[str, str]],
                 name: str,
                 version: Optional[str] = None):
    """Находит пакет по его имени и опционально по версии"""
    candidates = [p for p in packages if p.get("P") == name]
    if not candidates:
        return None
    if version is None:
        return candidates[0]
    for pkg in candidates:
        if pkg.get("V") == version:
            return pkg
    return None


def extract_dependencies(pkg: Dict[str, str]):
    """Извлекает прямые зависимости"""
    deps_raw = pkg.get("D", "")
    if not deps_raw:
        return []
    return [d for d in deps_raw.split() if d]


def main():
    print("=== Получение зависимостей пакета Alpine Linux (APK) ===\n")

    argv = sys.argv
    repo_url = argv[2].strip()
    if not repo_url:
        print("[ERROR] URL не указан")
        sys.exit(1)

    pkg_name = str(sys.argv[1])
    if not pkg_name:
        print("[ERROR] Имя пакета не указано")
        sys.exit(1)

    pkg_version = None if argv[3].lower() in ["last", "l", "-"] else argv[3]

    try:
        archive = download_apkindex(repo_url)
        content = extract_apkindex(archive)
        packages = parse_apkindex(content)
        print(f"[INFO] Всего пакетов в индексе: {len(packages)}")

        pkg = find_package(packages, pkg_name, pkg_version)
        if pkg is None:
            print(f"[ERROR] Пакет '{pkg_name}'"
                  + (f" версии '{pkg_version}'" if pkg_version else "")
                  + " не найден в репозитории")
            sys.exit(2)

        print(f"\n[RESULT] Найден пакет:")
        print(f"  Имя:    {pkg.get('P')}")
        print(f"  Версия: {pkg.get('V')}")
        if pkg.get("D"):
            print(f"  Кол-во зависимостей: {len(pkg.get('D').split())}")

        deps = extract_dependencies(pkg)
        print(f"\n[RESULT] Прямые зависимости ({len(deps)}):")
        if not deps:
            print("  (нет зависимостей)")
        else:
            for d in deps:
                print(f"  - {d}")

    except urllib.error.URLError as e:
        print(f"[ERROR] Ошибка сети: {e}")
        sys.exit(3)
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        sys.exit(4)


if __name__ == "__main__":
    if get_args():
        main()