import urllib.request
import tarfile
import io
import sys
from typing import Optional, Dict, List, Set
from collections import deque


def get_args():  # Проверка корректности аргументов
    if len(sys.argv) > 4:
        try:
            if sys.argv[4].lower() not in ["true", "false"]:
                raise ValueError
        except ValueError:
            print("[ERROR] Неправильный параметр режима работы с репозиторием")
            return False

    if len(sys.argv) > 6:
        try:
            if sys.argv[6].lower() not in ["true", "false"]:
                raise ValueError
        except ValueError:
            print("[ERROR] Неправильный параметр режима вывода зависимостей")
            return False

    return True


def download_apkindex(repo_url: str):  # Скачивает APK файл
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


def extract_apkindex(archive_bytes: bytes):  # Распаковывает APK файл и возвращает его содержимое
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.name in ("APKINDEX", "APKINDEX.tar.gz/APKINDEX"):
                f = tar.extractfile(member)
                if f is not None:
                    return f.read().decode("utf-8", errors="replace")
        raise RuntimeError("Файл APKINDEX не найден в архиве")


def parse_apkindex(content: str):  # Парсит содержимое APK файла в список словарей
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
                 version: Optional[str] = None):  # Находит пакет по его имени и опционально по версии
    candidates = [p for p in packages if p.get("P") == name]
    if not candidates:
        return None
    if version is None:
        return candidates[0]
    for pkg in candidates:
        if pkg.get("V") == version:
            return pkg
    return None


def extract_dependencies(pkg: Dict[str, str]):  # Извлекает прямые зависимости
    deps_raw = pkg.get("D", "")
    if not deps_raw:
        return []
    return [d for d in deps_raw.split() if d]


def load_test_repository(file_path: str):  # Загрузка тестового репозитория из файла
    packages = []
    current = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    if current:
                        packages.append(current)
                        current = {}
                    continue

                if ':' in line:
                    key, _, value = line.partition(':')
                    key = key.strip()
                    value = value.strip()
                    if key in current:
                        current[key] = current[key] + " " + value
                    else:
                        current[key] = value

            if current:
                packages.append(current)

        print(f"[INFO] Загружено {len(packages)} пакетов из тестового файла")
        return packages

    except FileNotFoundError:
        print(f"[ERROR] Файл '{file_path}' не найден")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Ошибка чтения файла: {e}")
        sys.exit(1)


def build_dependency_graph(packages: List[Dict[str, str]]):  # Построение графа зависимостей
    graph = {}

    for pkg in packages:
        name = pkg.get("P", "")
        deps = extract_dependencies(pkg)
        graph[name] = deps

    return graph


def bfs_with_recursion(graph: Dict[str, List[str]],
                       start: str,
                       visited: Optional[Set[str]] = None,
                       depth: int = 0,
                       max_depth: int = 100):  # BFS с рекурией для построения дерева зависимостей
    if visited is None:
        visited = set()

    result = {}

    if depth >= max_depth or start in visited:
        if start in visited:
            print(f"  [WARNING] Обнаружена циклическая зависимость: {start}")
        return result

    visited.add(start)

    neighbors = graph.get(start, [])

    if neighbors:
        result[start] = neighbors

        for neighbor in neighbors:
            sub_result = bfs_with_recursion(graph, neighbor, visited.copy(), depth + 1, max_depth)
            result.update(sub_result)

    return result


def get_all_transitive_deps(graph: Dict[str, List[str]],
                            start: str):  # Возвращает все транзитивные зависимости используя BFS
    all_deps = set()
    queue = deque([start])
    visited = {start}

    while queue:
        current = queue.popleft()
        deps = graph.get(current, [])

        for dep in deps:
            if dep not in visited:
                visited.add(dep)
                all_deps.add(dep)
                queue.append(dep)
            elif dep in all_deps:
                # Циклическая зависимость
                pass

    return all_deps


def print_ascii_tree(graph: Dict[str, List[str]],
                     start: str,
                     prefix: str = "",
                     is_last: bool = True,
                     visited: Optional[Set[str]] = None,
                     depth: int = 0,
                     max_depth: int = 50):  # Выводит дерево зависимостей
    if visited is None:
        visited = set()

    # Проверяем на циклическую зависимость
    if start in visited:
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{start} (циклическая зависимость)")
        return

    visited.add(start)

    if depth == 0:
        connector = ""
    else:
        connector = "└── " if is_last else "├── "

    print(f"{prefix}{connector}{start}")

    deps = graph.get(start, [])

    if not deps:
        return

    if depth > 0:
        new_prefix = prefix + ("    " if is_last else "│   ")
    else:
        new_prefix = prefix

    for i, dep in enumerate(deps):
        is_last_dep = (i == len(deps) - 1)
        print_ascii_tree(graph, dep, new_prefix, is_last_dep, visited.copy(), depth + 1, max_depth)


def print_dependency_summary(graph: Dict[str, List[str]], start: str):  # Выводит сводку о зависимостях пакета
    print(f"\n{'=' * 60}")
    print(f"Граф зависимостей для пакета: {start}")
    print(f"{'=' * 60}\n")

    direct_deps = graph.get(start, [])
    print(f"Прямые зависимости ({len(direct_deps)}):")
    for dep in direct_deps:
        print(f"  - {dep}")

    all_deps = get_all_transitive_deps(graph, start)
    print(f"\nВсе транзитивные зависимости ({len(all_deps)}):")
    if all_deps:
        for dep in sorted(all_deps):
            print(f"  - {dep}")
    else:
        print("  (нет дополнительных зависимостей)")

    print(f"\nДерево зависимостей:")
    print("-" * 60)
    print_ascii_tree(graph, start)
    print("-" * 60)


def create_test_repository_file(file_path: str):  # Создает пример тестового файла репозитория
    test_content = """
P:A
V:1.0
D:B C

P:B
V:1.0
D:D E

P:C
V:1.0
D:E F

P:D
V:1.0

P:E
V:1.0
D:F

P:F
V:1.0

P:G
V:1.0
D:H

P:H
V:1.0
D:G
"""

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)

    print(f"[INFO] Создан тестовый файл: {file_path}")


def main():
    print("=== Получение зависимостей пакета Alpine Linux (APK) ===\n")

    test_mode = False
    test_file = None

    if len(sys.argv) > 4 and sys.argv[4].lower() == "true":
        test_mode = True
        if len(sys.argv) > 2:
            test_file = sys.argv[2].strip()
        else:
            sys.exit(1)

    pkg_name = str(sys.argv[1])
    if not pkg_name:
        print("[ERROR] Имя пакета не указано")
        sys.exit(1)

    pkg_version = None if len(sys.argv) <= 3 or sys.argv[3].lower() in ["last", "l", "-"] else sys.argv[3]

    try:
        if test_mode:
            print(f"[INFO] Режим тестирования: загрузка из файла {test_file}")
            packages = load_test_repository(test_file)
        else:
            repo_url = sys.argv[2].strip()
            if not repo_url:
                print("[ERROR] URL не указан")
                sys.exit(1)

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

        graph = build_dependency_graph(packages)

        print_dependency_summary(graph, pkg_name)

        print(f"\nПроверка на циклические зависимости:")
        all_deps = get_all_transitive_deps(graph, pkg_name)
        cycles_found = False

        for dep in all_deps:
            dep_deps = graph.get(dep, [])
            if pkg_name in dep_deps:
                print(f"  [CYCLE] {pkg_name} -> ... -> {dep} -> {pkg_name}")
                cycles_found = True

        if not cycles_found:
            print("  Циклические зависимости не обнаружены")

    except urllib.error.URLError as e:
        print(f"[ERROR] Ошибка сети: {e}")
        sys.exit(3)
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(4)


if __name__ == "__main__":  # Для демонстрации: создаем тестовый файл если он не существует
    if len(sys.argv) > 4 and sys.argv[4].lower() == "true":
        if len(sys.argv) > 2:
            test_file = sys.argv[2]
            import os

            if not os.path.exists(test_file):
                create_test_repository_file(test_file)

    if get_args():
        main()