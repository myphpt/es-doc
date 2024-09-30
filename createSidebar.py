
import os
filePath = './Elasticsearch'
list = []
with open('_sidebar.md','w',encoding='utf-8') as fp:
    for path, dir_lst, file_lst in os.walk(filePath):
        # print(path, dir_lst, file_lst)
        for file_name in file_lst:
            line = '[' + file_name.split('.')[0] + '](' + os.path.join(path, file_name) + ')'
            print(line)
            fp.write(line + '\n')

    