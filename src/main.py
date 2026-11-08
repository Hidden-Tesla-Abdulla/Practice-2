import sys


def get_args():
    argv = sys.argv
    if len(argv) > 1:
        print(f"Имя анализируемого пакета: {argv[1]}")
    if len(sys.argv) > 2:
        print(f"Репозиторий: {argv[2]}" )
    if len(sys.argv) > 3:
        if argv[3].lower() in ["last", "-", "l"]:
            print("Версия пакета: последняя")
        else:
            print(f"Версия пакета: {argv[3]}")
    if len(argv) > 4:
        try:
            if argv[4].lower() not in ["true", "false"]:
                raise ValueError
            print(f"Режим работы с тестовым репозиторием {argv[4]}")
        except ValueError:
            print("[ERROR] Неправильный параметр режима работы с репозиторием")
    if len(argv) > 5:
        try:
            if argv[5].lower() not in ["true", "false"]:
                raise ValueError
            print(f"Режим вывода зависимостей в формате ASCII-дерева: {argv[5]}")
        except ValueError:
            print("[ERROR] Неправильный параметр режима вывода зависимостей")
    if len(argv) > 6:
        print(f"Имя сгенерированного файла с изображением графа: {argv[6]}")

def main():
    get_args()

if __name__ == "__main__":
    main()