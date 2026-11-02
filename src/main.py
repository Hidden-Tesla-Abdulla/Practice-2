import sys


def get_args():
    if len(sys.argv) > 1:
        print(f"Имя анализируемого пакета: {sys.argv[1]}")
    if len(sys.argv) > 2:
        print(f"Репозиторий: {sys.argv[2]}" )
    if len(sys.argv) > 3:
        if sys.argv[3].lower() in ["last", "-", "l"]:
            print("Версия пакета: последняя")
        else:
            print(f"Версия пакета: {sys.argv[3]}")
    if len(sys.argv) > 4:
        try:
            if sys.argv[4].lower() not in ["true", "false"]:
                raise ValueError
            print(f"Режим работы с тестовым репозиторием {sys.argv[4]}")
        except ValueError:
            print("[ERROR] Неправильный параметр режима работы с репозиторием")
    if len(sys.argv) > 5:
        try:
            if sys.argv[5].lower() not in ["true", "false"]:
                raise ValueError
            print(f"Режим вывода зависимостей в формате ASCII-дерева: {sys.argv[5]}")
        except ValueError:
            print("[ERROR] Неправильный параметр режима вывода зависимостей")
    if len(sys.argv) > 6:
        print(f"Имя сгенерированного файла с изображением графа: {sys.argv[6]}")

def main():
    get_args()

if __name__ == "__main__":
    main() # arbuz