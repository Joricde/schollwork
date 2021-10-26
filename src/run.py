# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import push


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    push.bot_start()

    # thread_1 = threading.Thread(target=remind.bot_start)
    # thread_2 = threading.Thread(target=push.get_message)
    # thread_1.start()
    # thread_2.start()
    # thread_1.join()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
